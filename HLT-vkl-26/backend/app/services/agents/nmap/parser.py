from xml.etree import ElementTree as ET

from app.services.agents.base import AgentParser


class NmapParser(AgentParser):
    agent_type = "nmap"

    def normalize(self, raw_output: str) -> dict:
        if self._looks_like_xml(raw_output):
            hosts = self._parse_xml(raw_output)
            return {"tool": self.agent_type, "format": "xml", "hosts": hosts, "record_count": len(hosts)}

        hosts = self._parse_key_value_lines(raw_output)
        return {"tool": self.agent_type, "format": "kv", "hosts": hosts, "record_count": len(hosts)}

    def extract_findings(self, raw_output: str) -> list[dict]:
        findings: list[dict] = []
        for host in self.normalize(raw_output)["hosts"]:
            host_address = host.get("host")
            for port_entry in host.get("ports", []):
                if port_entry.get("state") != "open":
                    continue
                findings.append(
                    {
                        "finding_code": f"NMAP-PORT-{port_entry['port']}",
                        "severity": "info",
                        "title": f"Open port {port_entry['port']} detected",
                        "description": (
                            f"Service {port_entry.get('service') or 'unknown'} is reachable on "
                            f"{host_address or 'the target'}."
                        ),
                        "port": port_entry["port"],
                        "protocol": port_entry.get("protocol"),
                        "service_name": port_entry.get("service"),
                        "evidence": f"Host {host_address} exposed port {port_entry['port']}/{port_entry.get('protocol')}",
                        "confidence": 95,
                        "status": "open",
                    }
                )
        return findings

    def _parse_xml(self, raw_output: str) -> list[dict]:
        root = ET.fromstring(raw_output)
        hosts: list[dict] = []

        for host_node in root.findall("host"):
            address_node = host_node.find("address")
            hostname_node = host_node.find("hostnames/hostname")
            status_node = host_node.find("status")
            ports: list[dict] = []

            for port_node in host_node.findall("ports/port"):
                state_node = port_node.find("state")
                service_node = port_node.find("service")
                script_nodes = port_node.findall("script")
                ports.append(
                    {
                        "port": self._to_int(port_node.get("portid")),
                        "protocol": port_node.get("protocol", "tcp"),
                        "state": state_node.get("state", "unknown") if state_node is not None else "unknown",
                        "service": service_node.get("name") if service_node is not None else None,
                        "product": service_node.get("product") if service_node is not None else None,
                        "version": service_node.get("version") if service_node is not None else None,
                        "scripts": [
                            {"id": script_node.get("id"), "output": script_node.get("output")}
                            for script_node in script_nodes
                        ],
                    }
                )

            hosts.append(
                {
                    "host": address_node.get("addr") if address_node is not None else None,
                    "hostname": hostname_node.get("name") if hostname_node is not None else None,
                    "status": status_node.get("state", "unknown") if status_node is not None else "unknown",
                    "ports": ports,
                }
            )

        return hosts

    def _parse_key_value_lines(self, raw_output: str) -> list[dict]:
        hosts_by_address: dict[str, dict] = {}

        for line in [line.strip() for line in raw_output.splitlines() if line.strip()]:
            parts = dict(item.split("=", 1) for item in line.split(";") if "=" in item)
            host = parts.get("host") or "unknown"
            host_entry = hosts_by_address.setdefault(
                host,
                {"host": host, "hostname": None, "status": "up", "ports": []},
            )
            host_entry["ports"].append(
                {
                    "port": self._to_int(parts.get("port")),
                    "protocol": parts.get("protocol", "tcp"),
                    "service": parts.get("service"),
                    "state": parts.get("state", "open"),
                    "product": parts.get("product"),
                    "version": parts.get("version"),
                    "scripts": [],
                }
            )

        return list(hosts_by_address.values())

    @staticmethod
    def _looks_like_xml(raw_output: str) -> bool:
        return raw_output.lstrip().startswith("<nmaprun")

    @staticmethod
    def _to_int(value: str | None) -> int | None:
        return int(value) if value and value.isdigit() else None
