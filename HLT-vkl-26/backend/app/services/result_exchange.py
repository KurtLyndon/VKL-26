import csv
import json
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Operation, OperationResultImportExport, OperationExecution, ScanResult, ScanResultFinding


EXPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "operation_results"


def _ensure_export_dir() -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    return EXPORT_DIR


def _operation_scan_results(db: Session, operation_id: int) -> tuple[list[ScanResult], list[ScanResultFinding]]:
    operation = db.get(Operation, operation_id)
    if not operation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")

    execution_ids = db.scalars(select(OperationExecution.id).where(OperationExecution.operation_id == operation_id)).all()
    if not execution_ids:
        return [], []

    scan_results = db.scalars(
        select(ScanResult)
        .where(ScanResult.operation_execution_id.in_(execution_ids))
        .order_by(ScanResult.id.asc())
    ).all()
    scan_result_ids = [item.id for item in scan_results]
    findings = []
    if scan_result_ids:
        findings = db.scalars(
            select(ScanResultFinding)
            .where(ScanResultFinding.scan_result_id.in_(scan_result_ids))
            .order_by(ScanResultFinding.id.asc())
        ).all()
    return scan_results, findings


def _serialize(scan_results: list[ScanResult], findings: list[ScanResultFinding]) -> dict:
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "scan_results": [
            {
                "id": item.id,
                "operation_execution_id": item.operation_execution_id,
                "task_execution_id": item.task_execution_id,
                "target_id": item.target_id,
                "agent_type": item.agent_type,
                "source_tool": item.source_tool,
                "raw_output": item.raw_output,
                "normalized_output_json": item.normalized_output_json,
                "detected_at": item.detected_at.isoformat() if item.detected_at else None,
                "parse_status": item.parse_status,
            }
            for item in scan_results
        ],
        "findings": [
            {
                "id": item.id,
                "scan_result_id": item.scan_result_id,
                "vulnerability_id": item.vulnerability_id,
                "finding_code": item.finding_code,
                "severity": item.severity,
                "title": item.title,
                "description": item.description,
                "port": item.port,
                "protocol": item.protocol,
                "service_name": item.service_name,
                "evidence": item.evidence,
                "confidence": item.confidence,
                "status": item.status,
            }
            for item in findings
        ],
    }


def export_operation_results(db: Session, operation_id: int, file_format: str) -> tuple[OperationResultImportExport, int]:
    file_format = file_format.lower()
    if file_format not in {"json", "csv", "xlsx"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported export format")

    scan_results, findings = _operation_scan_results(db, operation_id)
    payload = _serialize(scan_results, findings)
    export_dir = _ensure_export_dir()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_name = f"operation-{operation_id}-results-{timestamp}.{file_format}"
    file_path = export_dir / file_name

    if file_format == "json":
        file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    elif file_format == "csv":
        with file_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "scan_result_id",
                    "operation_execution_id",
                    "task_execution_id",
                    "target_id",
                    "agent_type",
                    "finding_id",
                    "finding_code",
                    "severity",
                    "title",
                    "port",
                    "protocol",
                    "service_name",
                    "status",
                ],
            )
            writer.writeheader()
            scan_result_map = {item.id: item for item in scan_results}
            for finding in findings:
                scan_result = scan_result_map.get(finding.scan_result_id)
                writer.writerow(
                    {
                        "scan_result_id": finding.scan_result_id,
                        "operation_execution_id": scan_result.operation_execution_id if scan_result else None,
                        "task_execution_id": scan_result.task_execution_id if scan_result else None,
                        "target_id": scan_result.target_id if scan_result else None,
                        "agent_type": scan_result.agent_type if scan_result else None,
                        "finding_id": finding.id,
                        "finding_code": finding.finding_code,
                        "severity": finding.severity,
                        "title": finding.title,
                        "port": finding.port,
                        "protocol": finding.protocol,
                        "service_name": finding.service_name,
                        "status": finding.status,
                    }
                )
    else:
        from openpyxl import Workbook

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "findings"
        worksheet.append(
            [
                "scan_result_id",
                "operation_execution_id",
                "task_execution_id",
                "target_id",
                "agent_type",
                "finding_id",
                "finding_code",
                "severity",
                "title",
                "port",
                "protocol",
                "service_name",
                "status",
            ]
        )
        scan_result_map = {item.id: item for item in scan_results}
        for finding in findings:
            scan_result = scan_result_map.get(finding.scan_result_id)
            worksheet.append(
                [
                    finding.scan_result_id,
                    scan_result.operation_execution_id if scan_result else None,
                    scan_result.task_execution_id if scan_result else None,
                    scan_result.target_id if scan_result else None,
                    scan_result.agent_type if scan_result else None,
                    finding.id,
                    finding.finding_code,
                    finding.severity,
                    finding.title,
                    finding.port,
                    finding.protocol,
                    finding.service_name,
                    finding.status,
                ]
            )
        workbook.save(file_path)

    history = OperationResultImportExport(
        operation_id=operation_id,
        action_type="export",
        file_name=file_name,
        file_path=str(file_path),
        file_format=file_format,
        status="completed",
        executed_at=datetime.utcnow(),
        note=f"Exported {len(scan_results)} scan results and {len(findings)} findings.",
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history, len(findings)


def import_operation_results(db: Session, operation_id: int, payload_json: dict) -> tuple[OperationResultImportExport, int, int]:
    operation = db.get(Operation, operation_id)
    if not operation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")

    scan_results_payload = payload_json.get("scan_results", [])
    findings_payload = payload_json.get("findings", [])
    id_map: dict[int, int] = {}

    for item in scan_results_payload:
        scan_result = ScanResult(
            operation_execution_id=item["operation_execution_id"],
            task_execution_id=item["task_execution_id"],
            target_id=item["target_id"],
            agent_type=item["agent_type"],
            source_tool=item.get("source_tool"),
            raw_output=item.get("raw_output"),
            normalized_output_json=item.get("normalized_output_json"),
            detected_at=datetime.fromisoformat(item["detected_at"]) if item.get("detected_at") else None,
            parse_status=item.get("parse_status", "success"),
        )
        db.add(scan_result)
        db.flush()
        if "id" in item:
            id_map[item["id"]] = scan_result.id

    for item in findings_payload:
        scan_result_finding = ScanResultFinding(
            scan_result_id=id_map.get(item["scan_result_id"], item["scan_result_id"]),
            vulnerability_id=item.get("vulnerability_id"),
            finding_code=item["finding_code"],
            severity=item.get("severity"),
            title=item["title"],
            description=item.get("description"),
            port=item.get("port"),
            protocol=item.get("protocol"),
            service_name=item.get("service_name"),
            evidence=item.get("evidence"),
            confidence=item.get("confidence"),
            status=item.get("status", "open"),
        )
        db.add(scan_result_finding)

    history = OperationResultImportExport(
        operation_id=operation_id,
        action_type="import",
        file_name=f"operation-{operation_id}-import-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json",
        file_path=None,
        file_format="json",
        status="completed",
        executed_at=datetime.utcnow(),
        note=f"Imported {len(scan_results_payload)} scan results and {len(findings_payload)} findings.",
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history, len(scan_results_payload), len(findings_payload)
