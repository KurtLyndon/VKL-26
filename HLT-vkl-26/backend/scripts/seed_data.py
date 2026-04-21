from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Agent, Operation, OperationTask, ReportTemplate, Target, Task, Vulnerability, VulnerabilityScript


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.scalar(select(Agent.id).limit(1)):
            print("Seed skipped: data already exists.")
            return

        agent_nmap = Agent(
            code="AG-NMAP-01",
            name="Nmap Agent 01",
            agent_type="nmap",
            host="agent-nmap-01",
            ip_address="192.168.10.21",
            port=8081,
            version="1.0.0",
            status="online",
        )
        agent_nuclei = Agent(
            code="AG-NUCLEI-01",
            name="Nuclei Agent 01",
            agent_type="nuclei",
            host="agent-nuclei-01",
            ip_address="192.168.10.22",
            port=8082,
            version="1.0.0",
            status="online",
        )

        task_nmap = Task(
            code="TASK-NMAP-TCP",
            name="TCP Port Discovery",
            agent_type="nmap",
            script_name="tcp_scan.py",
            script_path="/opt/hlt/tasks/tcp_scan.py",
            description="Quet port TCP co ban cho target network.",
            version="1.0.0",
            input_schema_json={"target": "cidr", "ports": "string"},
            output_schema_json={"hosts": "array", "ports": "array"},
        )
        task_nuclei = Task(
            code="TASK-NUCLEI-WEB",
            name="Web Vulnerability Discovery",
            agent_type="nuclei",
            script_name="web_vuln.py",
            script_path="/opt/hlt/tasks/web_vuln.py",
            description="Quet template nuclei cho web target.",
            version="1.0.0",
            input_schema_json={"target": "url", "templates": "array"},
            output_schema_json={"findings": "array"},
        )

        operation = Operation(
            code="OP-INTERNAL-WEEKLY",
            name="Weekly Internal Assessment",
            description="Operation mau cho kiem thu dinh ky he thong noi bo.",
            schedule_type="cron",
            schedule_config_json={"expression": "0 1 * * 1"},
            is_active=True,
        )

        target_network = Target(
            code="TGT-DC-NET",
            name="Domain Controller Segment",
            target_type="network",
            ip_range="192.168.10.0/24",
            description="Mang noi bo chua cac may chu dich vu quan trong.",
        )
        target_web = Target(
            code="TGT-PORTAL",
            name="Internal Portal",
            target_type="web",
            domain="portal.internal.local",
            description="Cong thong tin noi bo.",
        )

        vuln = Vulnerability(
            code="CVE-2024-DEMO-0001",
            title="Demo Internal RCE",
            level=4,
            threat="Co the dan den thuc thi lenh tu xa tren dich vu noi bo.",
            proposal="Cap nhat ban va han che truy cap den dich vu quan tri.",
            poc_file_name="demo_rce_check.py",
            description="Ban ghi mau de dev giao dien va quy trinh quan ly CVE.",
        )

        db.add_all([agent_nmap, agent_nuclei, task_nmap, task_nuclei, operation, target_network, target_web, vuln])
        db.flush()

        db.add_all(
            [
                OperationTask(
                    operation_id=operation.id,
                    task_id=task_nmap.id,
                    order_index=1,
                    input_override_json={"ports": "1-1024"},
                    continue_on_error=False,
                ),
                OperationTask(
                    operation_id=operation.id,
                    task_id=task_nuclei.id,
                    order_index=2,
                    input_override_json={"templates": ["cves", "default-logins"]},
                    continue_on_error=True,
                ),
                VulnerabilityScript(
                    vulnerability_id=vuln.id,
                    script_name="demo_rce_check.py",
                    script_type="py",
                    script_content='print("safe poc placeholder")',
                    version="1.0.0",
                    is_active=True,
                ),
                ReportTemplate(
                    code="RPT-WEEKLY-SUMMARY",
                    name="Weekly Security Summary",
                    report_type="weekly",
                    filter_config_json={"severity": ["critical", "high", "medium"]},
                    layout_config_json={"sections": ["overview", "findings", "targets"]},
                ),
            ]
        )

        db.commit()
        print("Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
