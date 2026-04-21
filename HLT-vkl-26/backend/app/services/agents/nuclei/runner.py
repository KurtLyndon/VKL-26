import json

from app.models import TaskExecution
from app.services.agents.runner_base import AgentRunner


class NucleiRunner(AgentRunner):
    agent_type = "nuclei"

    def run(self, task_execution: TaskExecution, target_value: str) -> str:
        records = [
            {
                "template-id": "CVE-2024-DEMO-0001",
                "matcher-name": "rce-check",
                "matched-at": f"http://{target_value}/login",
                "type": "http",
                "ip": target_value,
                "scheme": "http",
                "info": {
                    "name": "Demo Internal RCE",
                    "description": "Demo finding emitted by mock nuclei runner.",
                    "severity": "high",
                    "classification": {
                        "cve-id": "CVE-2024-DEMO-0001",
                        "cvss-score": "8.8",
                    },
                },
                "extracted-results": ["admin portal exposed"],
            }
        ]
        return "\n".join(json.dumps(record) for record in records)
