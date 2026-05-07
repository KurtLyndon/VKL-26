from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Operation, OperationExecution, ScanResult, ScanResultFinding, Target, Vulnerability
from app.schemas.resources import (
    FindingFilterOptionsResponse,
    FindingManagementRead,
    FindingOperationOption,
    FindingStatusOption,
    FindingTargetOption,
)

FINDING_STATUS_LABELS = {
    "open": "open",
    "confirmed": "confirmed",
    "in_progress": "in_progress",
    "resolved": "resolved",
    "false_positive": "false_positive",
    "risk_accepted": "risk_accepted",
    "reopened": "reopened",
}

FINDING_STATUS_HELP_TEXTS = {
    "open": "Finding mới ghi nhận, chưa được xác nhận hoặc xử lý.",
    "confirmed": "Finding đã được analyst xác nhận là nguy cơ thật.",
    "in_progress": "Finding đang trong quá trình xử lý hoặc xác minh bổ sung.",
    "resolved": "Finding đã được xử lý xong và không còn tồn tại sau khi kiểm tra lại.",
    "false_positive": "Finding được xác định là cảnh báo nhầm, không phải nguy cơ thật.",
    "risk_accepted": "Finding là nguy cơ thật nhưng đã được chấp nhận rủi ro.",
    "reopened": "Finding đã bị mở lại sau khi từng đóng hoặc chấp nhận rủi ro.",
}

FINDING_STATUS_TRANSITIONS = {
    "open": {"confirmed", "false_positive", "risk_accepted"},
    "confirmed": {"in_progress", "false_positive", "risk_accepted"},
    "in_progress": {"open", "resolved", "false_positive", "risk_accepted"},
    "resolved": {"reopened"},
    "false_positive": {"reopened"},
    "risk_accepted": {"reopened"},
    "reopened": {"confirmed", "false_positive", "risk_accepted"},
}


@dataclass
class FindingJoinedRow:
    finding: ScanResultFinding
    scan_result: ScanResult
    target: Target
    execution: OperationExecution
    operation: Operation
    vulnerability: Vulnerability | None


def level_to_severity(level: int | None) -> str:
    if level is None:
        return "unknown"
    if level >= 4:
        return "critical"
    if level == 3:
        return "high"
    if level == 2:
        return "medium"
    if level == 1:
        return "low"
    return "unknown"


def ensure_vulnerability_stub(db: Session, code: str) -> Vulnerability:
    normalized_code = (code or "").strip()
    if not normalized_code:
        raise ValueError("Thiếu mã CVE/vulnerability để tạo record mặc định.")

    vulnerability = db.scalar(select(Vulnerability).where(Vulnerability.code == normalized_code))
    if vulnerability is not None:
        return vulnerability

    vulnerability = Vulnerability(
        code=normalized_code,
        title=normalized_code,
        level=0,
        threat=None,
        proposal=None,
        poc_file_name=None,
        poc_text=None,
        description=None,
    )
    db.add(vulnerability)
    db.flush()
    return vulnerability


def get_status_options() -> list[FindingStatusOption]:
    return [
        FindingStatusOption(
            value=value,
            label=FINDING_STATUS_LABELS[value],
            help_text=FINDING_STATUS_HELP_TEXTS[value],
            allowed_next_statuses=sorted(FINDING_STATUS_TRANSITIONS.get(value, set())),
        )
        for value in FINDING_STATUS_LABELS
    ]


def ensure_status_transition(current_status: str | None, next_status: str, *, force: bool = False) -> str:
    normalized_current = (current_status or "open").strip().lower()
    normalized_next = (next_status or "").strip().lower()

    if normalized_next not in FINDING_STATUS_LABELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trạng thái finding không hợp lệ.",
        )

    if force or normalized_current == normalized_next:
        return normalized_next

    allowed = FINDING_STATUS_TRANSITIONS.get(normalized_current, set())
    if normalized_next not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể chuyển trạng thái từ {normalized_current} sang {normalized_next}.",
        )
    return normalized_next


def resolve_vulnerability_for_finding(
    db: Session,
    *,
    vulnerability_id: int | None = None,
    finding_code: str | None = None,
) -> Vulnerability | None:
    if vulnerability_id:
        vulnerability = db.get(Vulnerability, vulnerability_id)
        if vulnerability is not None:
            return vulnerability

    normalized_code = (finding_code or "").strip()
    if not normalized_code:
        return None

    return db.scalar(select(Vulnerability).where(Vulnerability.code == normalized_code))


def apply_vulnerability_defaults(
    db: Session,
    finding: ScanResultFinding,
    *,
    vulnerability: Vulnerability | None = None,
) -> Vulnerability | None:
    vulnerability = vulnerability or resolve_vulnerability_for_finding(
        db,
        vulnerability_id=finding.vulnerability_id,
        finding_code=finding.finding_code,
    )

    if vulnerability is not None:
        finding.vulnerability_id = vulnerability.id
        finding.finding_code = vulnerability.code
        finding.title = vulnerability.code
        finding.severity = level_to_severity(vulnerability.level)
        finding.description = vulnerability.threat or vulnerability.description
    else:
        finding.title = finding.finding_code or finding.title or "Finding"

    finding.evidence = None
    return vulnerability


def get_finding_status_help_text(status_value: str) -> str:
    normalized = (status_value or "open").strip().lower()
    return FINDING_STATUS_HELP_TEXTS.get(normalized, "Trạng thái finding hiện tại.")


def _base_finding_stmt() -> Select:
    return (
        select(ScanResultFinding, ScanResult, Target, OperationExecution, Operation, Vulnerability)
        .join(ScanResult, ScanResult.id == ScanResultFinding.scan_result_id)
        .join(Target, Target.id == ScanResult.target_id)
        .join(OperationExecution, OperationExecution.id == ScanResult.operation_execution_id)
        .join(Operation, Operation.id == OperationExecution.operation_id)
        .outerjoin(Vulnerability, Vulnerability.id == ScanResultFinding.vulnerability_id)
    )


def _extract_ip_address(scan_result: ScanResult) -> str | None:
    payload = scan_result.normalized_output_json or {}
    if isinstance(payload, dict):
        ip_value = payload.get("ip") or payload.get("host") or payload.get("address")
        if isinstance(ip_value, str):
            return ip_value
    return None


def _operation_label(execution: OperationExecution, operation: Operation) -> str:
    parts = [execution.execution_code]
    if operation.code and operation.code not in parts:
        parts.append(operation.code)
    if execution.year:
        suffix = str(execution.year)
        if execution.quarter:
            suffix += f" / Q{execution.quarter}"
        elif execution.week:
            suffix += f" / W{execution.week}"
        parts.append(suffix)
    return " | ".join(part for part in parts if part)


def serialize_finding_row(row: FindingJoinedRow) -> FindingManagementRead:
    finding = row.finding
    vulnerability = row.vulnerability
    derived_severity = level_to_severity(vulnerability.level) if vulnerability else finding.severity
    derived_description = vulnerability.threat or vulnerability.description if vulnerability else finding.description
    normalized_status = (finding.status or "open").strip().lower()

    return FindingManagementRead(
        id=finding.id,
        scan_result_id=finding.scan_result_id,
        vulnerability_id=finding.vulnerability_id,
        operation_execution_id=row.execution.id,
        target_id=row.target.id,
        ip_address=_extract_ip_address(row.scan_result),
        finding_code=finding.finding_code,
        title=finding.finding_code,
        severity=derived_severity,
        description=derived_description,
        port=finding.port,
        protocol=finding.protocol,
        service_name=finding.service_name,
        note=finding.note,
        evidence=finding.evidence,
        confidence=finding.confidence,
        status=normalized_status,
        status_help_text=get_finding_status_help_text(normalized_status),
        allowed_next_statuses=sorted(FINDING_STATUS_TRANSITIONS.get(normalized_status, set())),
        operation_label=_operation_label(row.execution, row.operation),
        target_label=row.target.name,
        poc_file_name=finding.poc_file_name,
        poc_file_path=finding.poc_file_path,
        poc_file_mime_type=finding.poc_file_mime_type,
        poc_file_size=finding.poc_file_size,
        first_seen_at=finding.first_seen_at,
        last_seen_at=finding.last_seen_at,
        created_at=finding.created_at,
        updated_at=finding.updated_at,
    )


def _materialize_rows(rows: list[tuple]) -> list[FindingManagementRead]:
    return [
        serialize_finding_row(
            FindingJoinedRow(
                finding=finding,
                scan_result=scan_result,
                target=target,
                execution=execution,
                operation=operation,
                vulnerability=vulnerability,
            )
        )
        for finding, scan_result, target, execution, operation, vulnerability in rows
    ]


def list_finding_records(
    db: Session,
    *,
    operation_execution_id: int | None = None,
    target_id: int | None = None,
    status_value: str | None = None,
) -> list[FindingManagementRead]:
    stmt = _base_finding_stmt()
    if operation_execution_id:
        stmt = stmt.where(ScanResult.operation_execution_id == operation_execution_id)
    if target_id:
        stmt = stmt.where(ScanResult.target_id == target_id)
    if status_value:
        stmt = stmt.where(ScanResultFinding.status == status_value.strip().lower())
    stmt = stmt.order_by(ScanResultFinding.id.desc())
    return _materialize_rows(db.execute(stmt).all())


def get_finding_record(db: Session, finding_id: int) -> FindingManagementRead:
    row = db.execute(_base_finding_stmt().where(ScanResultFinding.id == finding_id)).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return _materialize_rows([row])[0]


def get_finding_filter_options(
    db: Session,
    *,
    operation_execution_id: int | None = None,
) -> FindingFilterOptionsResponse:
    operation_rows = db.execute(
        select(OperationExecution, Operation)
        .join(ScanResult, ScanResult.operation_execution_id == OperationExecution.id)
        .join(ScanResultFinding, ScanResultFinding.scan_result_id == ScanResult.id)
        .join(Operation, Operation.id == OperationExecution.operation_id)
        .distinct(OperationExecution.id)
        .order_by(OperationExecution.id.desc())
    ).all()

    target_stmt = (
        select(Target)
        .join(ScanResult, ScanResult.target_id == Target.id)
        .join(ScanResultFinding, ScanResultFinding.scan_result_id == ScanResult.id)
        .distinct(Target.id)
        .order_by(Target.id.asc())
    )
    if operation_execution_id:
        target_stmt = target_stmt.where(ScanResult.operation_execution_id == operation_execution_id)

    operation_options = [
        FindingOperationOption(id=execution.id, label=_operation_label(execution, operation))
        for execution, operation in operation_rows
    ]
    target_options = [
        FindingTargetOption(id=target.id, label=f"{target.id} - {target.name}")
        for target in db.scalars(target_stmt).all()
    ]

    return FindingFilterOptionsResponse(
        operations=operation_options,
        targets=target_options,
        statuses=get_status_options(),
    )
