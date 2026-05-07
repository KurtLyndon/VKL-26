from __future__ import annotations

import json
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Operation, OperationExecution, ScanResult, ScanResultFinding, Target, TaskExecution, Vulnerability
from app.services.findings import apply_vulnerability_defaults, ensure_vulnerability_stub, level_to_severity
from app.services.targets import normalize_target_ip_range, resolve_target_ip_entries, target_contains_ip


def build_pkt_scan_folder_name(operation: Operation, execution: OperationExecution) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "-", operation.name or operation.code).strip("-").lower() or operation.code.lower()
    date_tag = (execution.started_at or datetime.utcnow()).strftime("%Y%m%d")
    tags: list[str] = [base]
    if execution.year:
        tags.append(f"y{execution.year}")
    if execution.quarter:
        tags.append(f"q{execution.quarter}")
    if execution.week:
        tags.append(f"w{execution.week}")
    tags.append(date_tag)
    return "-".join(tags)[:120]


def build_pkt_scan_entries(db: Session, target_ids: list[int]) -> tuple[list[str], list[Target]]:
    selected_targets = db.scalars(select(Target).where(Target.id.in_(target_ids)).order_by(Target.id.asc())).all() if target_ids else []
    seen = set()
    entries: list[str] = []
    for target in selected_targets:
        for entry in resolve_target_ip_entries(target.ip_range):
            normalized = normalize_target_ip_range(entry) or entry
            if normalized and normalized not in seen:
                seen.add(normalized)
                entries.append(normalized)
    return entries, selected_targets


def _build_duplicate_target_notes(selected_targets: list[Target]) -> dict[int, str]:
    targets_by_range: dict[str, list[Target]] = {}
    for target in selected_targets:
        normalized_range = normalize_target_ip_range(target.ip_range)
        if not normalized_range:
            continue
        targets_by_range.setdefault(normalized_range, []).append(target)

    notes: dict[int, str] = {}
    for targets in targets_by_range.values():
        if len(targets) < 2:
            continue
        for target in targets:
            other_names = [item.name for item in targets if item.id != target.id]
            if other_names:
                notes[target.id] = f"Trùng dải IP với {', '.join(other_names)}"
    return notes


def ingest_pkt_scan_output(db: Session, task_execution: TaskExecution, raw_output: str) -> dict:
    payload = json.loads(raw_output)
    records = payload.get("scan_results") or []
    warnings = payload.get("warnings") or []
    operation_execution = db.get(OperationExecution, task_execution.operation_execution_id)
    selected_target_ids = operation_execution.selected_target_ids_json or [] if operation_execution else []
    selected_targets = db.scalars(select(Target).where(Target.id.in_(selected_target_ids)).order_by(Target.id.asc())).all() if selected_target_ids else []
    duplicate_target_notes = _build_duplicate_target_notes(selected_targets)
    vulnerability_rows = db.scalars(select(Vulnerability)).all()
    vulnerability_by_code = {item.code: item for item in vulnerability_rows}

    created_target_ids: set[int] = set()
    created_scan_results = 0
    created_findings = 0
    unmatched_vuln_codes: set[str] = set()

    for record in records:
        ip_value = str(record.get("ip") or "").strip()
        if not ip_value:
            continue

        matched_targets = [target for target in selected_targets if target_contains_ip(target.ip_range, ip_value)]
        if matched_targets:
            target = matched_targets[0]
            target_note = duplicate_target_notes.get(target.id)
        else:
            target = db.scalar(select(Target).where(Target.code == "target_unmapped_historical"))
            if target is None:
                continue
            target_note = "Không map được IP scan vào target đã chọn"

        created_target_ids.add(target.id)

        scan_result = ScanResult(
            operation_execution_id=task_execution.operation_execution_id,
            task_execution_id=task_execution.id,
            target_id=target.id,
            agent_type="nmap",
            source_tool="pkt_scannerv1.py",
            raw_output=json.dumps(record, ensure_ascii=False),
            normalized_output_json={
                "ip": ip_value,
                "port": record.get("port"),
                "protocol": record.get("protocol") or "tcp",
                "service": record.get("service"),
                "version": record.get("version"),
                "vuln_codes": record.get("vuln_codes") or [],
                "note": target_note,
                "folder_name": payload.get("folder_name"),
            },
            detected_at=datetime.utcnow(),
            parse_status="success",
        )
        db.add(scan_result)
        db.flush()
        created_scan_results += 1

        for vuln_code in record.get("vuln_codes") or []:
            vulnerability = vulnerability_by_code.get(vuln_code)
            if vulnerability is None:
                vulnerability = ensure_vulnerability_stub(db, vuln_code)
                vulnerability_by_code[vuln_code] = vulnerability
                unmatched_vuln_codes.add(vuln_code)

            finding = ScanResultFinding(
                scan_result_id=scan_result.id,
                vulnerability_id=vulnerability.id,
                finding_code=vulnerability.code,
                severity=level_to_severity(vulnerability.level),
                title=vulnerability.code,
                description=vulnerability.threat or vulnerability.description,
                port=record.get("port"),
                protocol=record.get("protocol") or "tcp",
                service_name=record.get("service") or None,
                note=record.get("version"),
                evidence=None,
                confidence=100,
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                status="open",
            )
            apply_vulnerability_defaults(db, finding, vulnerability=vulnerability)
            db.add(finding)
            created_findings += 1

    for target in selected_targets:
        if target.id in created_target_ids:
            continue
        note_message = duplicate_target_notes.get(target.id) or "Không phát hiện IP public"
        placeholder_scan_result = ScanResult(
            operation_execution_id=task_execution.operation_execution_id,
            task_execution_id=task_execution.id,
            target_id=target.id,
            agent_type="nmap",
            source_tool="pkt_scannerv1.py",
            raw_output=json.dumps(
                {
                    "target_id": target.id,
                    "target_name": target.name,
                    "note": note_message,
                    "placeholder": True,
                },
                ensure_ascii=False,
            ),
            normalized_output_json={
                "target_id": target.id,
                "target_name": target.name,
                "folder_name": payload.get("folder_name"),
                "note": note_message,
                "placeholder": True,
            },
            detected_at=datetime.utcnow(),
            parse_status="success",
        )
        db.add(placeholder_scan_result)
        created_scan_results += 1

    summary = {
        "result_code": payload.get("result_code"),
        "folder_name": payload.get("folder_name"),
        "output_dir": payload.get("output_dir"),
        "file_inventory": payload.get("file_inventory") or [],
        "live_host_count": len(payload.get("live_hosts") or []),
        "created_scan_results": created_scan_results,
        "created_findings": created_findings,
        "unmatched_vuln_codes": sorted(unmatched_vuln_codes),
        "warnings": warnings,
    }
    return summary
