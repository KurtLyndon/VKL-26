from app.services.agents.base import AgentParser


class NmapParser(AgentParser):
    agent_type = "nmap"

    def normalize(self, raw_output: str) -> dict:
        lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
        hosts: list[dict] = []

        for line in lines:
            parts = dict(item.split("=", 1) for item in line.split(";") if "=" in item)
            hosts.append(
                {
                    "host": parts.get("host"),
                    "port": self._to_int(parts.get("port")),
                    "protocol": parts.get("protocol", "tcp"),
                    "service": parts.get("service"),
                    "state": parts.get("state", "open"),
                }
            )

        return {"tool": self.agent_type, "hosts": hosts, "record_count": len(hosts)}

    def extract_findings(self, raw_output: str) -> list[dict]:
        findings: list[dict] = []
        for entry in self.normalize(raw_output)["hosts"]:
            if not entry.get("port"):
                continue
            findings.append(
                {
                    "finding_code": f"NMAP-PORT-{entry['port']}",
                    "severity": "info",
                    "title": f"Open port {entry['port']} detected",
                    "description": f"Service {entry.get('service') or 'unknown'} is reachable on the target.",
                    "port": entry["port"],
                    "protocol": entry.get("protocol"),
                    "service_name": entry.get("service"),
                    "evidence": f"Host {entry.get('host')} exposed port {entry['port']}",
                    "confidence": 90,
                    "status": "open",
                }
            )
        return findings

    @staticmethod
    def _to_int(value: str | None) -> int | None:
        return int(value) if value and value.isdigit() else None
