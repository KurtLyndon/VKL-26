from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ScanResult, ScanResultFinding, Vulnerability
from app.services.agents.registry import get_parser


def _find_vulnerability_id(db: Session, finding: dict) -> int | None:
    candidate_codes = [
        finding.get("finding_code"),
        finding.get("title"),
        finding.get("evidence"),
    ]
    vulnerabilities = db.scalars(select(Vulnerability)).all()
    for vulnerability in vulnerabilities:
        for candidate in candidate_codes:
            if not candidate:
                continue
            if vulnerability.code and vulnerability.code.lower() in str(candidate).lower():
                return vulnerability.id
    return None


def normalize_and_store_scan_result(
    db: Session,
    *,
    agent_type: str,
    source_tool: str | None,
    raw_output: str,
    operation_execution_id: int,
    task_execution_id: int,
    target_id: int,
    detected_at: datetime | None = None,
) -> tuple[ScanResult, list[ScanResultFinding]]:
    parser = get_parser(agent_type)
    normalized_output = parser.normalize(raw_output)

    scan_result = ScanResult(
        operation_execution_id=operation_execution_id,
        task_execution_id=task_execution_id,
        target_id=target_id,
        agent_type=agent_type,
        source_tool=source_tool or agent_type,
        raw_output=raw_output,
        normalized_output_json=normalized_output,
        detected_at=detected_at,
        parse_status="success",
    )
    db.add(scan_result)
    db.flush()

    findings: list[ScanResultFinding] = []
    for finding in parser.extract_findings(raw_output):
        vulnerability_id = _find_vulnerability_id(db, finding)
        finding_record = ScanResultFinding(
            scan_result_id=scan_result.id,
            vulnerability_id=vulnerability_id,
            **finding,
        )
        db.add(finding_record)
        findings.append(finding_record)

    return scan_result, findings
