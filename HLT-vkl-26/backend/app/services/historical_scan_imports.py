import csv
import json
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, time
from io import StringIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agent, Operation, OperationExecution, OperationTask, ScanImportBatch, ScanResult, ScanResultFinding, Target, Task, TaskExecution, Vulnerability
from app.schemas.resources import HistoricalImportCandidateTarget, HistoricalImportCommitResponse, HistoricalImportIpMappingItem, HistoricalImportPreviewResponse, OperationLaunchRequest, ScanImportBatchRead
from app.services.findings import apply_vulnerability_defaults, level_to_severity
from app.services.targets import normalize_target_ip_range, target_contains_ip


HISTORICAL_IMPORT_AGENT_CODE = "AG-SYSTEM-01"
HISTORICAL_IMPORT_TASK_CODE = "TASK-HIST-SERVICES-VULNS-IMPORT"
HISTORICAL_IMPORT_OPERATION_CODE = "OP-HIST-SCAN-IMPORT"
UNMAPPED_TARGET_CODE = "target_unmapped_historical"
UNMAPPED_TARGET_NAME = "Unmapped Historical Scan"
UNMAPPED_SENTINEL = "__UNMAPPED__"


@dataclass
class ParsedServiceRow:
    row_number: int
    ip: str
    port: int
    service: str
    version: str | None
    vuln_codes: list[str]


@dataclass
class MappingResolution:
    ip: str
    status: str
    matched_targets: list[Target]
    resolved_target: Target | None


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


def _decode_csv_bytes(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1258"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("latin-1")


def _normalize_header(value: str) -> str:
    return (value or "").strip().lower()


def _parse_port(raw_value: str, row_number: int, warnings: list[str]) -> int | None:
    try:
        return int((raw_value or "").strip())
    except (TypeError, ValueError):
        warnings.append(f"Dòng {row_number}: port không hợp lệ `{raw_value}`.")
        return None


def parse_services_vulns_csv(file_name: str, content: bytes) -> tuple[list[ParsedServiceRow], list[str]]:
    if not file_name.lower().endswith(".csv"):
        raise ValueError("Phase 1 chỉ hỗ trợ file CSV kiểu services_vulns.csv.")

    text = _decode_csv_bytes(content)
    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames:
        raise ValueError("File CSV không có header.")

    headers = {_normalize_header(item): item for item in reader.fieldnames}
    required = {"ip", "port", "service", "version", "vulns"}
    missing = sorted(required - set(headers.keys()))
    if missing:
        raise ValueError(f"Thiếu cột bắt buộc trong CSV: {', '.join(missing)}.")

    rows: list[ParsedServiceRow] = []
    warnings: list[str] = []
    current_ip = ""

    for index, raw_row in enumerate(reader, start=2):
        ip_value = (raw_row.get(headers["ip"]) or "").strip()
        if ip_value:
            current_ip = ip_value
        elif not current_ip:
            warnings.append(f"Dòng {index}: cột IP trống và không có IP trước đó để carry forward.")
            continue

        port_value = _parse_port(raw_row.get(headers["port"]) or "", index, warnings)
        if port_value is None:
            continue

        service_value = (raw_row.get(headers["service"]) or "").strip()
        version_value = (raw_row.get(headers["version"]) or "").strip() or None
        vuln_raw = (raw_row.get(headers["vulns"]) or "").strip()
        vuln_codes = [item.strip() for item in vuln_raw.split(";") if item.strip()]

        rows.append(
            ParsedServiceRow(
                row_number=index,
                ip=current_ip,
                port=port_value,
                service=service_value,
                version=version_value,
                vuln_codes=vuln_codes,
            )
        )

    return rows, warnings


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        if len(value) == 10:
            return datetime.combine(datetime.fromisoformat(value).date(), time.min)
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"Ngày không hợp lệ: {value}") from error


def _resolve_ip_mappings(
    selected_targets: list[Target],
    ips: list[str],
    manual_mapping: dict[str, str | int | None] | None = None,
) -> list[MappingResolution]:
    targets_by_id = {target.id: target for target in selected_targets}
    manual_mapping = manual_mapping or {}
    items: list[MappingResolution] = []

    for ip in ips:
        matches = [target for target in selected_targets if target_contains_ip(target.ip_range, ip)]
        manual_value = manual_mapping.get(ip)
        resolved_target = None
        status = "unmapped"

        if manual_value not in (None, "", UNMAPPED_SENTINEL):
            try:
                resolved_target = targets_by_id.get(int(manual_value))
            except (TypeError, ValueError):
                resolved_target = None
            if resolved_target is not None:
                status = "manual"
        elif manual_value == UNMAPPED_SENTINEL:
            status = "unmapped"
        elif len(matches) == 1:
            resolved_target = matches[0]
            status = "auto"
        elif len(matches) > 1:
            status = "ambiguous"
        else:
            status = "unmapped"

        items.append(
            MappingResolution(
                ip=ip,
                status=status,
                matched_targets=matches,
                resolved_target=resolved_target,
            )
        )

    return items


def _ensure_import_runtime_entities(db: Session) -> tuple[Agent, Task, Operation, OperationTask]:
    agent = db.scalar(select(Agent).where(Agent.code == HISTORICAL_IMPORT_AGENT_CODE))
    if agent is None:
        agent = Agent(
            code=HISTORICAL_IMPORT_AGENT_CODE,
            name="System Agent",
            agent_type="system",
            host="localhost",
            ip_address="127.0.0.1",
            port=0,
            version="1.0.0",
            status="online",
        )
        db.add(agent)
        db.flush()

    task = db.scalar(select(Task).where(Task.code == HISTORICAL_IMPORT_TASK_CODE))
    if task is None:
        task = Task(
            code=HISTORICAL_IMPORT_TASK_CODE,
            name="P.K.T Scanner Result Import",
            agent_type="system",
            script_name="historical_scan_importer",
            script_path="internal://historical_scan_importer",
            description="Import dữ liệu scan lịch sử từ file services_vulns.csv.",
            version="1.0.0",
            is_active=True,
            input_schema_json={"file": "csv", "metadata": "object", "target_ids": "array"},
            output_schema_json={"scan_results": "array", "findings": "array"},
        )
        db.add(task)
        db.flush()
    else:
        task.name = "P.K.T Scanner Result Import"
        task.agent_type = "system"
        task.script_name = "historical_scan_importer"
        task.script_path = "internal://historical_scan_importer"
        task.description = "Import dữ liệu scan lịch sử từ file services_vulns.csv."
        task.version = "1.0.0"
        task.is_active = True

    operation = db.scalar(select(Operation).where(Operation.code == HISTORICAL_IMPORT_OPERATION_CODE))
    if operation is None:
        operation = Operation(
            code=HISTORICAL_IMPORT_OPERATION_CODE,
            name="Historical Scan Import",
            description="Operation hệ thống dùng để import kết quả scan lịch sử.",
            schedule_type="none",
            schedule_config_json=None,
            is_active=True,
        )
        db.add(operation)
        db.flush()

    operation_task = db.scalar(
        select(OperationTask).where(
            OperationTask.operation_id == operation.id,
            OperationTask.task_id == task.id,
        )
    )
    if operation_task is None:
        operation_task = OperationTask(
            operation_id=operation.id,
            task_id=task.id,
            order_index=1,
            input_override_json={"source": "services_vulns.csv"},
            continue_on_error=False,
        )
        db.add(operation_task)
        db.flush()

    return agent, task, operation, operation_task


def _ensure_unmapped_target(db: Session) -> Target:
    target = db.scalar(select(Target).where(Target.code == UNMAPPED_TARGET_CODE))
    if target is None:
        target = Target(
            code=UNMAPPED_TARGET_CODE,
            name=UNMAPPED_TARGET_NAME,
            target_type="network",
            ip_range=None,
            domain=None,
            description="Target hệ thống để gắn các IP import lịch sử chưa map được.",
        )
        db.add(target)
        db.flush()
    return target


def _build_preview_payload(
    db: Session,
    file_name: str,
    content: bytes,
    batch_code: str,
    selected_target_ids: list[int],
    manual_mapping: dict[str, str | int | None] | None = None,
) -> tuple[HistoricalImportPreviewResponse, list[ParsedServiceRow], list[MappingResolution], dict[str, Vulnerability], list[str]]:
    if not batch_code.strip():
        raise ValueError("Thiếu tên đợt quét / mã đợt quét.")
    if not selected_target_ids:
        raise ValueError("Cần chọn ít nhất một Target trong phạm vi import.")

    rows, warnings = parse_services_vulns_csv(file_name, content)
    if not rows:
        raise ValueError("File services_vulns.csv không có dòng dữ liệu hợp lệ để import.")
    selected_targets = db.scalars(select(Target).where(Target.id.in_(selected_target_ids)).order_by(Target.id.desc())).all()
    if not selected_targets:
        raise ValueError("Không tìm thấy Target nào trong danh sách đã chọn.")

    unique_ips = list(OrderedDict.fromkeys(row.ip for row in rows))
    mapping_items = _resolve_ip_mappings(selected_targets, unique_ips, manual_mapping)
    mapping_by_ip = {item.ip: item for item in mapping_items}

    all_vuln_codes = [code for row in rows for code in row.vuln_codes]
    vulnerability_rows = db.scalars(select(Vulnerability).where(Vulnerability.code.in_(set(all_vuln_codes)))).all() if all_vuln_codes else []
    vulnerability_by_code = {item.code: item for item in vulnerability_rows}
    unmatched_codes = sorted({code for code in all_vuln_codes if code not in vulnerability_by_code})

    preview = HistoricalImportPreviewResponse(
        source_file_name=file_name,
        batch_code=batch_code.strip(),
        total_rows=len(rows),
        detected_ips=len(unique_ips),
        service_rows=len(rows),
        finding_count=len(all_vuln_codes),
        matched_vulnerability_count=sum(1 for code in all_vuln_codes if code in vulnerability_by_code),
        unmatched_vulnerability_count=sum(1 for code in all_vuln_codes if code not in vulnerability_by_code),
        unmatched_vulnerability_codes=unmatched_codes,
        mapped_ip_count=sum(1 for item in mapping_items if item.status in {"auto", "manual"}),
        manual_required_ip_count=sum(1 for item in mapping_items if item.status == "ambiguous"),
        unmapped_ip_count=sum(1 for item in mapping_items if item.status == "unmapped"),
        mapping_items=[
            HistoricalImportIpMappingItem(
                ip=item.ip,
                status=item.status,
                matched_target_ids=[target.id for target in item.matched_targets],
                matched_targets=[
                    HistoricalImportCandidateTarget(
                        id=target.id,
                        code=target.code,
                        name=target.name,
                        ip_range=target.ip_range,
                    )
                    for target in item.matched_targets
                ],
                resolved_target_id=item.resolved_target.id if item.resolved_target else None,
                resolved_target_name=item.resolved_target.name if item.resolved_target else None,
            )
            for item in mapping_items
        ],
        warning_messages=warnings,
    )

    return preview, rows, mapping_items, vulnerability_by_code, warnings


def preview_services_vulns_import(
    db: Session,
    *,
    file_name: str,
    content: bytes,
    batch_code: str,
    selected_target_ids: list[int],
    manual_mapping: dict[str, str | int | None] | None = None,
) -> HistoricalImportPreviewResponse:
    preview, _rows, _mapping_items, _vulnerability_by_code, _warnings = _build_preview_payload(
        db,
        file_name=file_name,
        content=content,
        batch_code=batch_code,
        selected_target_ids=selected_target_ids,
        manual_mapping=manual_mapping,
    )
    return preview


def commit_services_vulns_import(
    db: Session,
    *,
    file_name: str,
    content: bytes,
    batch_code: str,
    year: int,
    quarter: int,
    week: int,
    scan_started_at: str | None,
    scan_finished_at: str | None,
    note: str | None,
    source_root_path: str | None,
    selected_target_ids: list[int],
    manual_mapping: dict[str, str | int | None] | None = None,
) -> HistoricalImportCommitResponse:
    preview, rows, mapping_items, vulnerability_by_code, warnings = _build_preview_payload(
        db,
        file_name=file_name,
        content=content,
        batch_code=batch_code,
        selected_target_ids=selected_target_ids,
        manual_mapping=manual_mapping,
    )
    if preview.unmatched_vulnerability_count > 0:
        raise ValueError(
            "Còn vuln code chưa match với bảng Vulnerability. Cần xử lý trước khi commit: "
            + ", ".join(preview.unmatched_vulnerability_codes)
        )

    unresolved_ips = [item.ip for item in mapping_items if item.status == "ambiguous"]
    if unresolved_ips:
        raise ValueError(
            "Còn IP map mơ hồ giữa nhiều Target. Hãy chọn Target thủ công hoặc đánh dấu unmapped: "
            + ", ".join(unresolved_ips[:20])
        )

    started_at = _parse_iso_datetime(scan_started_at)
    finished_at = _parse_iso_datetime(scan_finished_at)
    agent, task, operation, operation_task = _ensure_import_runtime_entities(db)
    unmapped_target = _ensure_unmapped_target(db)

    execution = OperationExecution(
        operation_id=operation.id,
        execution_code=f"HIST-{batch_code.strip()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"[:100],
        trigger_type="manual",
        status="completed",
        started_at=started_at or datetime.utcnow(),
        finished_at=finished_at or datetime.utcnow(),
        summary_json={
            "source_file_name": file_name,
            "source_root_path": source_root_path,
            "year": year,
            "quarter": quarter,
            "week": week,
            "service_rows": preview.service_rows,
            "finding_count": preview.finding_count,
        },
        year=year,
        quarter=quarter,
        week=week,
        note=note,
        source_root_path=source_root_path,
        selected_target_ids_json=selected_target_ids,
    )
    db.add(execution)
    db.flush()

    task_execution = TaskExecution(
        operation_execution_id=execution.id,
        operation_task_id=operation_task.id,
        task_id=task.id,
        agent_id=agent.id,
        status="completed",
        input_data_json={
            "batch_code": batch_code.strip(),
            "selected_target_ids": selected_target_ids,
            "source_file_name": file_name,
            "year": year,
            "quarter": quarter,
            "week": week,
        },
        output_data_json={
            "service_rows": preview.service_rows,
            "finding_count": preview.finding_count,
        },
        raw_log="P.K.T scanner result import completed.",
        started_at=execution.started_at,
        finished_at=execution.finished_at,
    )
    db.add(task_execution)
    db.flush()

    mapping_by_ip = {item.ip: item for item in mapping_items}
    selected_targets = db.scalars(select(Target).where(Target.id.in_(selected_target_ids)).order_by(Target.id.asc())).all()
    duplicate_target_notes = _build_duplicate_target_notes(selected_targets)
    created_target_ids: set[int] = set()
    created_scan_results = 0
    created_findings = 0

    for row in rows:
        mapping = mapping_by_ip[row.ip]
        target = mapping.resolved_target or unmapped_target
        target_note = duplicate_target_notes.get(target.id)
        created_target_ids.add(target.id)

        scan_result = ScanResult(
            operation_execution_id=execution.id,
            task_execution_id=task_execution.id,
            target_id=target.id,
            agent_type="system",
            source_tool="services_vulns.csv",
            raw_output=json.dumps(
                {
                    "ip": row.ip,
                    "port": row.port,
                    "service": row.service,
                    "version": row.version,
                    "vulns": row.vuln_codes,
                    "row_number": row.row_number,
                    "note": target_note,
                },
                ensure_ascii=False,
            ),
            normalized_output_json={
                "ip": row.ip,
                "port": row.port,
                "service": row.service,
                "version": row.version,
                "vulns": row.vuln_codes,
                "batch_code": batch_code.strip(),
                "note": target_note,
            },
            detected_at=finished_at or execution.finished_at,
            parse_status="success",
        )
        db.add(scan_result)
        db.flush()
        created_scan_results += 1

        for vuln_code in row.vuln_codes:
            vulnerability = vulnerability_by_code[vuln_code]
            finding = ScanResultFinding(
                scan_result_id=scan_result.id,
                vulnerability_id=vulnerability.id,
                finding_code=vulnerability.code,
                severity=level_to_severity(vulnerability.level),
                title=vulnerability.code,
                description=vulnerability.threat or vulnerability.description,
                port=row.port,
                protocol="tcp",
                service_name=row.service or None,
                note=row.version,
                evidence=None,
                confidence=100,
                first_seen_at=started_at or execution.started_at,
                last_seen_at=finished_at or execution.finished_at,
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
            operation_execution_id=execution.id,
            task_execution_id=task_execution.id,
            target_id=target.id,
            agent_type="system",
            source_tool="services_vulns.csv",
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
                "batch_code": batch_code.strip(),
                "note": note_message,
                "placeholder": True,
            },
            detected_at=finished_at or execution.finished_at,
            parse_status="success",
        )
        db.add(placeholder_scan_result)
        created_scan_results += 1

    batch = ScanImportBatch(
        operation_execution_id=execution.id,
        task_execution_id=task_execution.id,
        batch_code=batch_code.strip(),
        scan_year=year,
        scan_quarter=quarter,
        scan_week=week,
        scan_started_at=started_at,
        scan_finished_at=finished_at,
        note=note,
        source_root_path=source_root_path,
        source_file_name=file_name,
        selected_target_ids_json=selected_target_ids,
        summary_json={
            "total_rows": preview.total_rows,
            "detected_ips": preview.detected_ips,
            "service_rows": preview.service_rows,
            "finding_count": preview.finding_count,
            "matched_vulnerability_count": preview.matched_vulnerability_count,
            "unmatched_vulnerability_count": preview.unmatched_vulnerability_count,
            "mapped_ip_count": preview.mapped_ip_count,
            "manual_required_ip_count": preview.manual_required_ip_count,
            "unmapped_ip_count": preview.unmapped_ip_count,
            "warnings": warnings,
        },
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    return HistoricalImportCommitResponse(
        batch=ScanImportBatchRead.model_validate(batch),
        created_scan_results=created_scan_results,
        created_findings=created_findings,
        auto_mapped_ip_count=sum(1 for item in mapping_items if item.status == "auto"),
        manually_mapped_ip_count=sum(1 for item in mapping_items if item.status == "manual"),
        unmapped_ip_count=sum(1 for item in mapping_items if item.status == "unmapped"),
    )
