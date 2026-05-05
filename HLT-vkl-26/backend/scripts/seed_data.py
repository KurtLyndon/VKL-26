from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Agent, Operation, OperationTask, ReportTemplate, Task
from database.migrations import apply_migrations
from scripts.import_targets_from_xlsx import import_workbook as import_targets_workbook
from scripts.import_vulnerabilities_from_xlsx import import_workbook as import_vulnerabilities_workbook


ROOT_DIR = Path(__file__).resolve().parents[1]
SEED_SOURCE_DIR = ROOT_DIR / "database" / "seed_sources"
VULNERABILITY_WORKBOOK = SEED_SOURCE_DIR / "1-Codes-v1.8-19-03-2026.xlsx"
TARGET_WORKBOOK = SEED_SOURCE_DIR / "2-Targets-basing.xlsx"


def get_or_create(db, model, lookup: dict, defaults: dict):
    item = db.scalar(select(model).filter_by(**lookup))
    if item is None:
        item = model(**lookup, **defaults)
        db.add(item)
        db.flush()
        return item, True

    for field, value in defaults.items():
        setattr(item, field, value)
    db.flush()
    return item, False


def ensure_core_seed_data() -> None:
    db = SessionLocal()
    try:
        agent_nmap, _ = get_or_create(
            db,
            Agent,
            {"code": "AG-NMAP-01"},
            {
                "name": "Nmap Agent 01",
                "agent_type": "nmap",
                "host": "agent-nmap-01",
                "ip_address": "192.168.10.21",
                "port": 8081,
                "version": "1.0.0",
                "status": "online",
            },
        )
        agent_nuclei, _ = get_or_create(
            db,
            Agent,
            {"code": "AG-NUCLEI-01"},
            {
                "name": "Nuclei Agent 01",
                "agent_type": "nuclei",
                "host": "agent-nuclei-01",
                "ip_address": "192.168.10.22",
                "port": 8082,
                "version": "1.0.0",
                "status": "online",
            },
        )
        agent_importer, _ = get_or_create(
            db,
            Agent,
            {"code": "AG-SYSTEM-01"},
            {
                "name": "System Agent",
                "agent_type": "system",
                "host": "localhost",
                "ip_address": "127.0.0.1",
                "port": 0,
                "version": "1.0.0",
                "status": "online",
            },
        )
        agent_verifier, _ = get_or_create(
            db,
            Agent,
            {"code": "AG-VULN-VERIFY-01"},
            {
                "name": "Vulnerability Verifier Agent",
                "agent_type": "vulnerability_verifier",
                "host": "localhost",
                "ip_address": "127.0.0.1",
                "port": 8091,
                "version": "1.0.0",
                "status": "online",
            },
        )

        task_nmap, _ = get_or_create(
            db,
            Task,
            {"code": "TASK-NMAP-TCP"},
            {
                "name": "TCP Port Discovery",
                "agent_type": "nmap",
                "script_name": "tcp_scan.py",
                "script_path": "/opt/hlt/tasks/tcp_scan.py",
                "description": "Quet port TCP co ban cho target network.",
                "version": "1.0.0",
                "is_active": True,
                "input_schema_json": {"target": "cidr", "ports": "string"},
                "output_schema_json": {"hosts": "array", "ports": "array"},
            },
        )
        task_nuclei, _ = get_or_create(
            db,
            Task,
            {"code": "TASK-NUCLEI-WEB"},
            {
                "name": "Web Vulnerability Discovery",
                "agent_type": "nuclei",
                "script_name": "web_vuln.py",
                "script_path": "/opt/hlt/tasks/web_vuln.py",
                "description": "Quet template nuclei cho web target.",
                "version": "1.0.0",
                "is_active": True,
                "input_schema_json": {"target": "url", "templates": "array"},
                "output_schema_json": {"findings": "array"},
            },
        )
        task_historical_import, _ = get_or_create(
            db,
            Task,
            {"code": "TASK-HIST-SERVICES-VULNS-IMPORT"},
            {
                "name": "P.K.T Scanner Result Import",
                "agent_type": "system",
                "script_name": "historical_scan_importer",
                "script_path": "internal://historical_scan_importer",
                "description": "Import dữ liệu scan lịch sử từ services_vulns.csv.",
                "version": "1.0.0",
                "is_active": True,
                "input_schema_json": {"file": "csv", "metadata": "object", "target_ids": "array"},
                "output_schema_json": {"scan_results": "array", "findings": "array"},
            },
        )
        task_vulnerability_verifying, _ = get_or_create(
            db,
            Task,
            {"code": "TASK-VULNERABILITY-VERIFY"},
            {
                "name": "Vulnerability Verifying",
                "agent_type": "vulnerability_verifier",
                "script_name": "verify_findings.py",
                "script_path": "/opt/hlt/tasks/verify_findings.py",
                "description": "Xac minh finding bang script PoC hoac text PoC cua CVE.",
                "version": "1.0.0",
                "is_active": True,
                "input_schema_json": {"operation_execution_id": "integer"},
                "output_schema_json": {"verified_count": "integer", "items": "array"},
            },
        )

        operation, _ = get_or_create(
            db,
            Operation,
            {"code": "OP-INTERNAL-WEEKLY"},
            {
                "name": "Weekly Internal Assessment",
                "description": "Operation mau cho kiem thu dinh ky he thong noi bo.",
                "schedule_type": "cron",
                "schedule_config_json": {"expression": "0 1 * * 1"},
                "is_active": True,
            },
        )
        operation_historical_import, _ = get_or_create(
            db,
            Operation,
            {"code": "OP-HIST-SCAN-IMPORT"},
            {
                "name": "Historical Scan Import",
                "description": "Operation hệ thống dùng để import kết quả scan lịch sử.",
                "schedule_type": "none",
                "schedule_config_json": None,
                "is_active": True,
            },
        )

        report_template, _ = get_or_create(
            db,
            ReportTemplate,
            {"code": "RPT-WEEKLY-SUMMARY"},
            {
                "name": "Weekly Security Summary",
                "report_type": "weekly",
                "filter_config_json": {"severity": ["critical", "high", "medium"]},
                "layout_config_json": {"sections": ["overview", "findings", "targets"]},
            },
        )

        operation_task_1 = db.scalar(
            select(OperationTask).where(
                OperationTask.operation_id == operation.id,
                OperationTask.task_id == task_nmap.id,
                OperationTask.order_index == 1,
            )
        )
        if operation_task_1 is None:
            db.add(
                OperationTask(
                    operation_id=operation.id,
                    task_id=task_nmap.id,
                    order_index=1,
                    input_override_json={"ports": "1-1024"},
                    continue_on_error=False,
                )
            )

        operation_task_2 = db.scalar(
            select(OperationTask).where(
                OperationTask.operation_id == operation.id,
                OperationTask.task_id == task_nuclei.id,
                OperationTask.order_index == 2,
            )
        )
        if operation_task_2 is None:
            db.add(
                OperationTask(
                    operation_id=operation.id,
                    task_id=task_nuclei.id,
                    order_index=2,
                    input_override_json={"templates": ["cves", "default-logins"]},
                    continue_on_error=True,
                )
            )

        operation_task_3 = db.scalar(
            select(OperationTask).where(
                OperationTask.operation_id == operation.id,
                OperationTask.task_id == task_vulnerability_verifying.id,
                OperationTask.order_index == 3,
            )
        )
        if operation_task_3 is None:
            db.add(
                OperationTask(
                    operation_id=operation.id,
                    task_id=task_vulnerability_verifying.id,
                    order_index=3,
                    input_override_json={"mode": "verify-findings"},
                    continue_on_error=True,
                )
            )

        operation_task_historical = db.scalar(
            select(OperationTask).where(
                OperationTask.operation_id == operation_historical_import.id,
                OperationTask.task_id == task_historical_import.id,
                OperationTask.order_index == 1,
            )
        )
        if operation_task_historical is None:
            db.add(
                OperationTask(
                    operation_id=operation_historical_import.id,
                    task_id=task_historical_import.id,
                    order_index=1,
                    input_override_json={"source": "services_vulns.csv"},
                    continue_on_error=False,
                )
            )

        db.commit()
        print(
            "Core seed completed:",
            agent_nmap.code,
            agent_nuclei.code,
            agent_importer.code,
            agent_verifier.code,
            task_nmap.code,
            task_nuclei.code,
            task_historical_import.code,
            task_vulnerability_verifying.code,
            operation.code,
            operation_historical_import.code,
            report_template.code,
        )
    finally:
        db.close()


def seed() -> None:
    apply_migrations()
    ensure_core_seed_data()

    if VULNERABILITY_WORKBOOK.exists():
        created, updated, copied_poc_files = import_vulnerabilities_workbook(VULNERABILITY_WORKBOOK)
        print(
            f"Seeded vulnerabilities from {VULNERABILITY_WORKBOOK.name}: "
            f"created={created}, updated={updated}, poc_files_copied={copied_poc_files}"
        )
    else:
        print(f"Skip vulnerability seed source: {VULNERABILITY_WORKBOOK} not found.")

    if TARGET_WORKBOOK.exists():
        created, updated = import_targets_workbook(TARGET_WORKBOOK)
        print(f"Seeded targets from {TARGET_WORKBOOK.name}: created={created}, updated={updated}")
    else:
        print(f"Skip target seed source: {TARGET_WORKBOOK} not found.")

    print("Seed completed successfully.")


if __name__ == "__main__":
    seed()
