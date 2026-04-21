import json

from app.models import TaskExecution
from app.services.agents.runner_base import AgentRunner


class AcunetixRunner(AgentRunner):
    agent_type = "acunetix"

    def run(self, task_execution: TaskExecution, target_value: str) -> str:
        return json.dumps(
            {
                "scan_id": f"scan-{task_execution.id}",
                "target": target_value,
                "vulnerabilities": [
                    {
                        "id": "AX-001",
                        "vt_name": "Directory Listing Enabled",
                        "title": "Directory Listing Enabled",
                        "severity": "medium",
                        "scheme": "http",
                        "port": 80,
                        "affects_url": f"http://{target_value}/uploads/",
                        "description": "Mock Acunetix finding emitted by local worker.",
                    }
                ],
            }
        )
