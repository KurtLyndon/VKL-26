from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import (
    Operation,
    OperationExecution,
    ScanImportBatch,
    ScanResult,
    ScanResultFinding,
    Target,
    TargetAttributeDefinition,
    TargetAttributeValue,
    TargetGroup,
    TargetGroupMapping,
    Vulnerability,
    VulnerabilityScript,
)
from app.schemas.resources import (
    ResultExplorerAttributeRead,
    ResultExplorerFilterOptionsResponse,
    ResultExplorerFindingDetail,
    ResultExplorerGroupRead,
    ResultExplorerItem,
    ResultExplorerOperationDetail,
    ResultExplorerOperationOption,
    ResultExplorerResponse,
    ResultExplorerScanDetail,
    ResultExplorerTargetDetail,
    ResultExplorerVulnerabilityDetail,
)
from app.services.findings import level_to_severity


def _json_dumps(value: Any, *, limit: int = 2000) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, indent=2)
    return text if len(text) <= limit else f"{text[:limit]}..."


def _normalized(scan_result: ScanResult) -> dict:
    payload = scan_result.normalized_output_json or {}
    return payload if isinstance(payload, dict) else {}


def _raw_json(scan_result: ScanResult) -> dict:
    if not scan_result.raw_output:
        return {}
    try:
        payload = json.loads(scan_result.raw_output)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_ip(scan_result: ScanResult) -> str | None:
    normalized = _normalized(scan_result)
    for key in ("ip", "host", "address"):
        value = normalized.get(key)
        if value:
            return str(value).strip()

    hosts = normalized.get("hosts")
    if isinstance(hosts, list) and hosts:
        first_host = hosts[0]
        if isinstance(first_host, dict):
            value = first_host.get("host") or first_host.get("ip") or first_host.get("address")
            if value:
                return str(value).strip()

    raw = _raw_json(scan_result)
    for key in ("ip", "host", "address"):
        value = raw.get(key)
        if value:
            return str(value).strip()
    return None


def _to_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _first_port_entry(scan_result: ScanResult) -> dict:
    normalized = _normalized(scan_result)
    ports = normalized.get("ports")
    if isinstance(ports, list) and ports:
        first = ports[0]
        if isinstance(first, dict):
            return first

    hosts = normalized.get("hosts")
    if isinstance(hosts, list) and hosts:
        first_host = hosts[0]
        if isinstance(first_host, dict):
            host_ports = first_host.get("ports")
            if isinstance(host_ports, list) and host_ports:
                first = host_ports[0]
                if isinstance(first, dict):
                    return first
    return {}


def _extract_port(scan_result: ScanResult, finding: ScanResultFinding | None = None) -> int | None:
    if finding and finding.port is not None:
        return finding.port
    normalized = _normalized(scan_result)
    value = normalized.get("port")
    if value not in (None, ""):
        return _to_int(value)
    return _to_int(_first_port_entry(scan_result).get("port"))


def _extract_protocol(scan_result: ScanResult, finding: ScanResultFinding | None = None) -> str | None:
    if finding and finding.protocol:
        return finding.protocol
    normalized = _normalized(scan_result)
    return normalized.get("protocol") or _first_port_entry(scan_result).get("protocol")


def _extract_service(scan_result: ScanResult, finding: ScanResultFinding | None = None) -> str | None:
    if finding and finding.service_name:
        return finding.service_name
    normalized = _normalized(scan_result)
    return normalized.get("service") or _first_port_entry(scan_result).get("service")


def _extract_version(scan_result: ScanResult) -> str | None:
    normalized = _normalized(scan_result)
    return normalized.get("version") or _first_port_entry(scan_result).get("version")


def _extract_note(scan_result: ScanResult) -> str | None:
    normalized = _normalized(scan_result)
    return normalized.get("note") or _raw_json(scan_result).get("note")


def _extract_batch_code(scan_result: ScanResult, batch: ScanImportBatch | None = None) -> str | None:
    if batch and batch.batch_code:
        return batch.batch_code
    normalized = _normalized(scan_result)
    return normalized.get("batch_code") or normalized.get("folder_name")


def _event_month(scan_result: ScanResult, execution: OperationExecution) -> int | None:
    value = scan_result.detected_at or execution.started_at or execution.finished_at or scan_result.created_at
    return value.month if isinstance(value, datetime) else None


def _operation_label(execution: OperationExecution, operation: Operation) -> str:
    parts = [operation.code or operation.name, execution.execution_code]
    if execution.year:
        period = str(execution.year)
        if execution.quarter:
            period += f" / Q{execution.quarter}"
        if execution.week:
            period += f" / W{execution.week}"
        parts.append(period)
    return " | ".join(part for part in parts if part)


def _base_stmt() -> Select:
    return (
        select(ScanResult, ScanResultFinding, Vulnerability, Target, OperationExecution, Operation)
        .select_from(ScanResult)
        .outerjoin(ScanResultFinding, ScanResultFinding.scan_result_id == ScanResult.id)
        .outerjoin(Vulnerability, Vulnerability.id == ScanResultFinding.vulnerability_id)
        .join(Target, Target.id == ScanResult.target_id)
        .join(OperationExecution, OperationExecution.id == ScanResult.operation_execution_id)
        .join(Operation, Operation.id == OperationExecution.operation_id)
    )


def _load_attribute_map(db: Session, target_ids: set[int]) -> dict[int, list[ResultExplorerAttributeRead]]:
    if not target_ids:
        return {}
    rows = db.execute(
        select(TargetAttributeValue, TargetAttributeDefinition)
        .join(TargetAttributeDefinition, TargetAttributeDefinition.id == TargetAttributeValue.attribute_definition_id)
        .where(TargetAttributeValue.target_id.in_(target_ids))
        .order_by(TargetAttributeDefinition.attribute_name.asc())
    ).all()
    grouped: dict[int, list[ResultExplorerAttributeRead]] = {}
    for value, definition in rows:
        grouped.setdefault(value.target_id, []).append(
            ResultExplorerAttributeRead(
                attribute_code=definition.attribute_code,
                attribute_name=definition.attribute_name,
                data_type=definition.data_type,
                value_text=value.value_text,
            )
        )
    return grouped


def _load_group_map(db: Session, target_ids: set[int]) -> dict[int, list[ResultExplorerGroupRead]]:
    if not target_ids:
        return {}
    rows = db.execute(
        select(TargetGroupMapping, TargetGroup)
        .join(TargetGroup, TargetGroup.id == TargetGroupMapping.target_group_id)
        .where(TargetGroupMapping.target_id.in_(target_ids))
        .order_by(TargetGroup.name.asc())
    ).all()
    grouped: dict[int, list[ResultExplorerGroupRead]] = {}
    for mapping, group in rows:
        grouped.setdefault(mapping.target_id, []).append(
            ResultExplorerGroupRead(id=group.id, code=group.code, name=group.name)
        )
    return grouped


def _load_batch_map(db: Session, execution_ids: set[int], task_execution_ids: set[int]) -> dict[tuple[int, int], ScanImportBatch]:
    if not execution_ids or not task_execution_ids:
        return {}
    batches = db.scalars(
        select(ScanImportBatch)
        .where(ScanImportBatch.operation_execution_id.in_(execution_ids))
        .where(ScanImportBatch.task_execution_id.in_(task_execution_ids))
    ).all()
    return {(item.operation_execution_id, item.task_execution_id): item for item in batches}


def _load_script_map(db: Session, vulnerability_ids: set[int]) -> dict[int, VulnerabilityScript]:
    if not vulnerability_ids:
        return {}
    scripts = db.scalars(
        select(VulnerabilityScript)
        .where(VulnerabilityScript.vulnerability_id.in_(vulnerability_ids))
        .where(VulnerabilityScript.is_active.is_(True))
        .order_by(VulnerabilityScript.vulnerability_id.asc(), VulnerabilityScript.id.desc())
    ).all()
    result: dict[int, VulnerabilityScript] = {}
    for script in scripts:
        result.setdefault(script.vulnerability_id, script)
    return result


def _matches_search(q: str, target: Target, scan_result: ScanResult, ip_address: str | None) -> bool:
    if not q:
        return True
    haystack = " ".join(
        str(value or "")
        for value in (
            target.name,
            target.code,
            target.ip_range,
            target.domain,
            ip_address,
            scan_result.raw_output,
            _json_dumps(scan_result.normalized_output_json, limit=4000),
        )
    ).lower()
    return q.lower() in haystack


def _build_item(
    *,
    scan_result: ScanResult,
    finding: ScanResultFinding | None,
    vulnerability: Vulnerability | None,
    target: Target,
    execution: OperationExecution,
    operation: Operation,
    attributes: list[ResultExplorerAttributeRead],
    groups: list[ResultExplorerGroupRead],
    batch: ScanImportBatch | None,
    active_script: VulnerabilityScript | None,
) -> ResultExplorerItem:
    ip_address = _extract_ip(scan_result)
    port = _extract_port(scan_result, finding)
    protocol = _extract_protocol(scan_result, finding)
    service = _extract_service(scan_result, finding)
    version = _extract_version(scan_result)
    month = _event_month(scan_result, execution)
    batch_code = _extract_batch_code(scan_result, batch)

    finding_detail = None
    if finding:
        finding_detail = ResultExplorerFindingDetail(
            finding_id=finding.id,
            finding_code=finding.finding_code,
            severity=finding.severity,
            status=finding.status,
            port=finding.port,
            protocol=finding.protocol,
            service_name=finding.service_name,
            note=finding.note,
            runtime_output=finding.runtime_output,
            confidence=finding.confidence,
            first_seen_at=finding.first_seen_at,
            last_seen_at=finding.last_seen_at,
            evidence_file_name=finding.evidence_file_name,
            evidence_file_path=finding.evidence_file_path,
            evidence_file_mime_type=finding.evidence_file_mime_type,
            evidence_file_size=finding.evidence_file_size,
        )

    vulnerability_detail = None
    if vulnerability:
        vulnerability_detail = ResultExplorerVulnerabilityDetail(
            vulnerability_id=vulnerability.id,
            code=vulnerability.code,
            title=vulnerability.title,
            level=vulnerability.level,
            severity=level_to_severity(vulnerability.level),
            threat=vulnerability.threat,
            proposal=vulnerability.proposal,
            description=vulnerability.description,
            evidence_text=vulnerability.evidence_text,
            poc_file_name=vulnerability.poc_file_name,
            active_script_name=active_script.script_name if active_script else None,
            active_script_type=active_script.script_type if active_script else None,
        )

    return ResultExplorerItem(
        row_id=f"{scan_result.id}:{finding.id if finding else 'scan'}",
        scan_result_id=scan_result.id,
        finding_id=finding.id if finding else None,
        target_name=target.name,
        ip_address=ip_address,
        finding_code=finding.finding_code if finding else None,
        severity=finding.severity if finding else None,
        finding_status=finding.status if finding else None,
        port=port,
        service=service,
        has_finding=finding is not None,
        operation=ResultExplorerOperationDetail(
            operation_id=operation.id,
            operation_code=operation.code,
            operation_name=operation.name,
            operation_execution_id=execution.id,
            execution_code=execution.execution_code,
            execution_status=execution.status,
            year=execution.year,
            quarter=execution.quarter,
            month=month,
            week=execution.week,
            batch_code=batch_code,
            source_file_name=batch.source_file_name if batch else None,
            source_root_path=execution.source_root_path,
        ),
        target=ResultExplorerTargetDetail(
            target_id=target.id,
            code=target.code,
            name=target.name,
            target_type=target.target_type,
            ip_range=target.ip_range,
            domain=target.domain,
            description=target.description,
            attributes=attributes,
            groups=groups,
        ),
        scan_result=ResultExplorerScanDetail(
            scan_result_id=scan_result.id,
            ip_address=ip_address,
            port=port,
            protocol=protocol,
            service=service,
            version=version,
            source_tool=scan_result.source_tool,
            detected_at=scan_result.detected_at,
            parse_status=scan_result.parse_status,
            note=_extract_note(scan_result),
            raw_summary=_json_dumps(scan_result.raw_output),
            normalized_summary=_json_dumps(scan_result.normalized_output_json),
            normalized_output_json=_normalized(scan_result),
        ),
        finding=finding_detail,
        vulnerability=vulnerability_detail,
    )


def get_result_explorer_filter_options(db: Session) -> ResultExplorerFilterOptionsResponse:
    rows = db.execute(
        select(OperationExecution, Operation, ScanResult)
        .join(Operation, Operation.id == OperationExecution.operation_id)
        .join(ScanResult, ScanResult.operation_execution_id == OperationExecution.id)
        .order_by(OperationExecution.id.desc())
    ).all()

    operations_by_id: dict[int, ResultExplorerOperationOption] = {}
    years: set[int] = set()
    quarters: set[int] = set()
    months: set[int] = set()
    weeks: set[int] = set()
    for execution, operation, scan_result in rows:
        operations_by_id.setdefault(
            operation.id,
            ResultExplorerOperationOption(id=operation.id, label=f"{operation.code} - {operation.name}"),
        )
        if execution.year:
            years.add(execution.year)
        if execution.quarter:
            quarters.add(execution.quarter)
        month = _event_month(scan_result, execution)
        if month:
            months.add(month)
        if execution.week:
            weeks.add(execution.week)

    return ResultExplorerFilterOptionsResponse(
        operations=list(operations_by_id.values()),
        years=sorted(years, reverse=True),
        quarters=sorted(quarters),
        months=sorted(months),
        weeks=sorted(weeks),
    )


def list_result_explorer_items(
    db: Session,
    *,
    operation_id: int | None = None,
    operation_execution_id: int | None = None,
    year: int | None = None,
    quarter: int | None = None,
    month: int | None = None,
    week: int | None = None,
    q: str | None = None,
    mode: str = "full",
) -> ResultExplorerResponse:
    normalized_mode = mode if mode in {"full", "threat"} else "full"
    stmt = _base_stmt()
    if normalized_mode == "threat":
        stmt = stmt.where(ScanResultFinding.id.is_not(None))
    if operation_id:
        stmt = stmt.where(Operation.id == operation_id)
    if operation_execution_id:
        stmt = stmt.where(OperationExecution.id == operation_execution_id)
    if year:
        stmt = stmt.where(OperationExecution.year == year)
    if quarter:
        stmt = stmt.where(OperationExecution.quarter == quarter)
    if week:
        stmt = stmt.where(OperationExecution.week == week)
    stmt = stmt.order_by(ScanResult.id.desc(), ScanResultFinding.id.desc())

    rows = db.execute(stmt).all()
    if month:
        rows = [
            row
            for row in rows
            if _event_month(row[0], row[4]) == month
        ]

    target_ids = {target.id for _scan, _finding, _vuln, target, _execution, _operation in rows}
    execution_ids = {execution.id for _scan, _finding, _vuln, _target, execution, _operation in rows}
    task_execution_ids = {scan.task_execution_id for scan, _finding, _vuln, _target, _execution, _operation in rows}
    vulnerability_ids = {vulnerability.id for _scan, _finding, vulnerability, _target, _execution, _operation in rows if vulnerability}
    attribute_map = _load_attribute_map(db, target_ids)
    group_map = _load_group_map(db, target_ids)
    batch_map = _load_batch_map(db, execution_ids, task_execution_ids)
    script_map = _load_script_map(db, vulnerability_ids)

    search_text = (q or "").strip()
    items: list[ResultExplorerItem] = []
    for scan_result, finding, vulnerability, target, execution, operation in rows:
        ip_address = _extract_ip(scan_result)
        if not _matches_search(search_text, target, scan_result, ip_address):
            continue
        batch = batch_map.get((scan_result.operation_execution_id, scan_result.task_execution_id))
        items.append(
            _build_item(
                scan_result=scan_result,
                finding=finding,
                vulnerability=vulnerability,
                target=target,
                execution=execution,
                operation=operation,
                attributes=attribute_map.get(target.id, []),
                groups=group_map.get(target.id, []),
                batch=batch,
                active_script=script_map.get(vulnerability.id) if vulnerability else None,
            )
        )

    return ResultExplorerResponse(items=items, total=len(items), mode=normalized_mode)
