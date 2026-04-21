import json

from app.services.agents.base import AgentParser


class AcunetixParser(AgentParser):
    agent_type = "acunetix"

    def normalize(self, raw_output: str) -> dict:
        parsed = self._parse_payload(raw_output)
        vulnerabilities = parsed.get("vulnerabilities", [])
        return {
            "tool": self.agent_type,
            "format": "json",
            "scan_id": parsed.get("scan_id"),
            "target": parsed.get("target"),
            "vulnerabilities": vulnerabilities,
            "record_count": len(vulnerabilities),
        }

    def extract_findings(self, raw_output: str) -> list[dict]:
        findings: list[dict] = []
        normalized = self.normalize(raw_output)
        for vuln in normalized.get("vulnerabilities", []):
            findings.append(
                {
                    "finding_code": vuln.get("vt_name") or vuln.get("id") or "ACUNETIX-FINDING",
                    "severity": str(vuln.get("severity", "medium")).lower(),
                    "title": vuln.get("title") or vuln.get("vt_name") or "Acunetix finding",
                    "description": vuln.get("description") or vuln.get("details") or "Finding imported from acunetix output.",
                    "port": self._to_int(vuln.get("port")),
                    "protocol": vuln.get("scheme"),
                    "service_name": "web",
                    "evidence": vuln.get("affects_url") or vuln.get("request"),
                    "confidence": 85,
                    "status": "open",
                }
            )
        return findings

    def _parse_payload(self, raw_output: str) -> dict:
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError:
            vulnerabilities = []
            for line in [line.strip() for line in raw_output.splitlines() if line.strip()]:
                parts = dict(item.split("=", 1) for item in line.split(";") if "=" in item)
                vulnerabilities.append(parts)
            return {"scan_id": None, "target": None, "vulnerabilities": vulnerabilities}

        if isinstance(parsed, list):
            return {"scan_id": None, "target": None, "vulnerabilities": parsed}

        if "vulnerabilities" in parsed:
            return parsed

        if "results" in parsed and isinstance(parsed["results"], list):
            return {
                "scan_id": parsed.get("scan_id"),
                "target": parsed.get("target"),
                "vulnerabilities": parsed["results"],
            }

        return {"scan_id": parsed.get("scan_id"), "target": parsed.get("target"), "vulnerabilities": []}

    @staticmethod
    def _to_int(value) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None
