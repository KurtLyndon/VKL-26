import json

from app.services.agents.base import AgentParser


class NucleiParser(AgentParser):
    agent_type = "nuclei"

    def normalize(self, raw_output: str) -> dict:
        findings = self._parse_lines(raw_output)
        return {"tool": self.agent_type, "findings": findings, "record_count": len(findings)}

    def extract_findings(self, raw_output: str) -> list[dict]:
        result: list[dict] = []
        for item in self._parse_lines(raw_output):
            result.append(
                {
                    "finding_code": item.get("template_id") or item.get("matcher_name") or "NUCLEI-FINDING",
                    "severity": item.get("severity", "medium"),
                    "title": item.get("name") or item.get("template") or "Nuclei finding",
                    "description": item.get("description") or "Finding imported from nuclei output.",
                    "port": self._extract_port(item.get("matched_at")),
                    "protocol": item.get("scheme"),
                    "service_name": item.get("service"),
                    "evidence": item.get("matched_at"),
                    "confidence": 85,
                    "status": "open",
                }
            )
        return result

    def _parse_lines(self, raw_output: str) -> list[dict]:
        findings: list[dict] = []
        for line in [line.strip() for line in raw_output.splitlines() if line.strip()]:
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError:
                parts = dict(item.split("=", 1) for item in line.split(";") if "=" in item)
                findings.append(parts)
        return findings

    @staticmethod
    def _extract_port(target: str | None) -> int | None:
        if not target or ":" not in target:
            return None
        tail = target.rsplit(":", 1)[-1]
        return int(tail) if tail.isdigit() else None
