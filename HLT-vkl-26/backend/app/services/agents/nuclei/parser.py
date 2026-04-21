import json
from urllib.parse import urlparse

from app.services.agents.base import AgentParser


class NucleiParser(AgentParser):
    agent_type = "nuclei"

    def normalize(self, raw_output: str) -> dict:
        findings = self._parse_lines(raw_output)
        return {"tool": self.agent_type, "format": "jsonl", "findings": findings, "record_count": len(findings)}

    def extract_findings(self, raw_output: str) -> list[dict]:
        result: list[dict] = []
        for item in self._parse_lines(raw_output):
            info = item.get("info", {})
            classification = info.get("classification", {})
            matcher_name = item.get("matcher_name")
            template_id = item.get("template_id")
            target = item.get("matched_at") or item.get("host")
            result.append(
                {
                    "finding_code": template_id or matcher_name or "NUCLEI-FINDING",
                    "severity": info.get("severity", "medium"),
                    "title": info.get("name") or template_id or "Nuclei finding",
                    "description": info.get("description") or "Finding imported from nuclei output.",
                    "port": self._extract_port(target),
                    "protocol": item.get("scheme") or self._extract_scheme(target),
                    "service_name": item.get("type"),
                    "evidence": item.get("extracted-results") or item.get("matcher-status") or target,
                    "confidence": 90 if classification.get("cvss-score") else 80,
                    "status": "open",
                }
            )
        return result

    def _parse_lines(self, raw_output: str) -> list[dict]:
        findings: list[dict] = []
        for line in [line.strip() for line in raw_output.splitlines() if line.strip()]:
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                parts = dict(item.split("=", 1) for item in line.split(";") if "=" in item)
                parsed = self._normalize_flat_fields(parts)
            else:
                parsed = self._normalize_json_fields(parsed)
            findings.append(parsed)
        return findings

    def _normalize_json_fields(self, item: dict) -> dict:
        info = item.get("info") or {}
        classification = info.get("classification") or {}
        return {
            "template_id": item.get("template-id") or item.get("templateID") or item.get("template_id"),
            "matcher_name": item.get("matcher-name") or item.get("matcher_name"),
            "matched_at": item.get("matched-at") or item.get("matched_at") or item.get("host"),
            "host": item.get("host"),
            "type": item.get("type"),
            "ip": item.get("ip"),
            "port": item.get("port"),
            "scheme": item.get("scheme") or self._extract_scheme(item.get("matched-at") or item.get("matched_at")),
            "info": {
                "name": info.get("name"),
                "description": info.get("description"),
                "severity": info.get("severity"),
                "classification": {
                    "cve-id": classification.get("cve-id") or classification.get("cve"),
                    "cvss-score": classification.get("cvss-score") or classification.get("cvss_score"),
                    "cwe-id": classification.get("cwe-id") or classification.get("cwe"),
                },
            },
            "extracted-results": item.get("extracted-results") or item.get("extracted_results"),
            "matcher-status": item.get("matcher-status") or item.get("matcher_status"),
        }

    def _normalize_flat_fields(self, parts: dict[str, str]) -> dict:
        severity = parts.get("severity", "medium")
        return {
            "template_id": parts.get("template_id"),
            "matcher_name": parts.get("matcher_name"),
            "matched_at": parts.get("matched_at"),
            "host": parts.get("host"),
            "type": parts.get("type"),
            "ip": parts.get("ip"),
            "port": parts.get("port"),
            "scheme": parts.get("scheme") or self._extract_scheme(parts.get("matched_at")),
            "info": {
                "name": parts.get("name"),
                "description": parts.get("description"),
                "severity": severity,
                "classification": {
                    "cve-id": parts.get("cve"),
                    "cvss-score": parts.get("cvss_score"),
                    "cwe-id": parts.get("cwe"),
                },
            },
            "extracted-results": parts.get("extracted_results"),
            "matcher-status": parts.get("matcher_status"),
        }

    @staticmethod
    def _extract_port(target: str | None) -> int | None:
        if not target:
            return None
        parsed = urlparse(target if "://" in target else f"http://{target}")
        if parsed.port:
            return parsed.port
        return 443 if parsed.scheme == "https" else 80 if parsed.scheme == "http" else None

    @staticmethod
    def _extract_scheme(target: str | None) -> str | None:
        if not target:
            return None
        parsed = urlparse(target if "://" in target else f"http://{target}")
        return parsed.scheme or None
