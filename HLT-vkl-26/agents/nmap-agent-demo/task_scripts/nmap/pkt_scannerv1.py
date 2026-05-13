#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    REQUESTS_AVAILABLE = True
except Exception:  # noqa: BLE001
    REQUESTS_AVAILABLE = False


RESULT_SUCCESS = 200
RESULT_INVALID_INPUT = 400
RESULT_MISSING_TOOL = 404
RESULT_OUTPUT_DIR_ERROR = 501
RESULT_SCAN_COMMAND_FAILED = 502
RESULT_PARSE_FAILED = 503
RESULT_UNKNOWN_ERROR = 500

TCP_DISCOVERY_SYN_PORTS = "22,80,135,139,443,445,3389"
UDP_CORE_PORTS = "53,69,123,161,500,4500,1900,3702,5353,5355,5060,47808"
HTTP_PORTS = {80, 443, 8080, 8000, 8443, 8008, 8081, 8888, 3000, 9080}
OUTPUT_FILES = [
    "discovery.gnmap",
    "fallback.gnmap",
    "alive_a.txt",
    "alive_b.txt",
    "hosts.txt",
    "tcp_full.gnmap",
    "tcp_full.nmap",
    "tcp_full.xml",
    "udpcore.gnmap",
    "udpcore.nmap",
    "udpcore.xml",
]

CVE_RE = re.compile(r"\b(CVE-\d{4}-\d{4,7})\b", re.I)
EXPLICIT_POS_RE = re.compile(
    r"\b(VULNERABLE|VULNERABLE:|authentication bypass|auth bypass|credentials found|default password|"
    r"weak password|password found|privilege escalation|remote code execution|RCE|unauthorized access|backdoor)\b",
    re.I,
)
WHITELIST_PATTERNS = [
    r"vuln",
    r"cve",
    r"^smb-vuln-",
    r"http-vuln",
    r"heartbleed",
    r"drown",
    r"snmp-",
    r"smb-.*vuln",
    r"sql-?inject",
    r"smb-vuln-ms17-010",
    r"sshv1-?vuln",
    r"mysql-.*(vuln|auth)",
]
WHITELIST_RE = [re.compile(item, re.I) for item in WHITELIST_PATTERNS]


def sanitize_field(value: str | None) -> str:
    if not value:
        return ""
    compact = " ".join(str(value).split())
    return compact.replace('"', "").replace(",", " ").strip()


def script_whitelisted(script_id: str | None) -> bool:
    if not script_id:
        return False
    return any(rx.search(script_id) for rx in WHITELIST_RE)


def extract_tokens_from_script(script_id: str | None, output: str | None) -> list[str]:
    sid = (script_id or "").strip()
    out = (output or "").strip()

    found_cves = []
    for item in CVE_RE.findall(out):
        normalized = item.upper()
        if normalized not in found_cves:
            found_cves.append(normalized)
    if found_cves:
        return found_cves

    if script_whitelisted(sid):
        return [sid]

    if EXPLICIT_POS_RE.search(out):
        if sid:
            return [sid]
        if re.search(r"community\s*'?(public)'?", out, re.I):
            return ["snmp-info"]
        return ["VULNERABLE"]

    if re.search(r"community\s*'?(public)'?", out, re.I):
        return ["snmp-info"]

    return []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PKT scanner runner")
    parser.add_argument("--targets", nargs="*", default=[], help="Danh sách IP/dải IP đầu vào")
    parser.add_argument("--targets-file", help="File JSON array hoặc text chứa danh sách IP/dải IP")
    parser.add_argument("--folder-name", required=True, help="Tên thư mục lưu kết quả scan")
    parser.add_argument("--output-root", default=".", help="Thư mục gốc để tạo folder-name")
    return parser.parse_args()


def load_targets(args: argparse.Namespace) -> list[str]:
    items = list(args.targets or [])
    if args.targets_file:
        file_path = Path(args.targets_file)
        if not file_path.exists():
            raise ValueError(f"Không tìm thấy file target: {file_path}")
        raw_text = file_path.read_text(encoding="utf-8")
        if file_path.suffix.lower() == ".json":
            parsed = json.loads(raw_text)
            if not isinstance(parsed, list):
                raise ValueError("File JSON target phải là mảng.")
            items.extend(str(item) for item in parsed if str(item).strip())
        else:
            for line in raw_text.splitlines():
                normalized = line.strip()
                if normalized:
                    items.append(normalized)

    normalized_items: list[str] = []
    seen = set()
    for item in items:
        compact = normalize_target_entry(item)
        if compact and compact not in seen:
            seen.add(compact)
            normalized_items.append(compact)
    return normalized_items


def normalize_target_entry(value: str) -> str:
    compact = re.sub(r"\s+", "", value or "")
    compact = compact.replace("_", "-")
    return compact.strip(",")


def ensure_output_dir(folder_name: str, output_root: str) -> Path:
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", folder_name).strip("-") or "pkt-scan"
    output_dir = Path(output_root).resolve() / safe_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_targets_file(output_dir: Path, targets: list[str]) -> Path:
    target_file = output_dir / "input_targets.txt"
    target_file.write_text("\n".join(targets) + "\n", encoding="utf-8")
    return target_file


def run_command(command: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    merged_output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    return result.returncode, merged_output


def parse_alive_from_discovery(gnmap_path: Path) -> list[str]:
    if not gnmap_path.exists():
        return []
    alive = []
    for line in gnmap_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("Host: ") and "Status: Up" in line:
            parts = line.split()
            if len(parts) >= 2 and parts[1] not in alive:
                alive.append(parts[1])
    return alive


def parse_alive_from_fallback(gnmap_path: Path) -> list[str]:
    if not gnmap_path.exists():
        return []
    alive = []
    for line in gnmap_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("Host: ") and "Ports:" in line and "open/" in line:
            parts = line.split()
            if len(parts) >= 2 and parts[1] not in alive:
                alive.append(parts[1])
    return alive


def parse_nmap_xml(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    root = ET.parse(path).getroot()
    for host in root.findall("host"):
        ip = None
        for address in host.findall("address"):
            if address.get("addrtype") == "ipv4":
                ip = address.get("addr")
                break
        if not ip:
            continue
        ports = host.find("ports")
        if ports is None:
            continue
        for port in ports.findall("port"):
            state = port.find("state")
            if state is None or (state.get("state") or "").lower() != "open":
                continue
            service_node = port.find("service")
            service = service_node.get("name") if service_node is not None else ""
            product = service_node.get("product") if service_node is not None else ""
            version = service_node.get("version") if service_node is not None else ""
            extrainfo = service_node.get("extrainfo") if service_node is not None else ""
            version_tokens = [token for token in [product, version, f"({extrainfo})" if extrainfo else ""] if token]
            vuln_codes: list[str] = []
            for script in port.findall("script"):
                tokens = extract_tokens_from_script(script.get("id"), script.get("output") or script.text or "")
                for token in tokens:
                    if token not in vuln_codes:
                        vuln_codes.append(token)
            rows.append(
                {
                    "ip": ip,
                    "port": int(port.get("portid", "0") or 0),
                    "protocol": port.get("protocol", "tcp"),
                    "service": service,
                    "version": " ".join(version_tokens).strip() or None,
                    "vuln_codes": vuln_codes,
                }
            )
    return rows


def parse_gnmap(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("Host: ") or "Ports:" not in line:
            continue
        left, ports_str = line.split("Ports:", 1)
        parts = left.split()
        ip = parts[1] if len(parts) >= 2 else ""
        for entry in ports_str.split(","):
            fields = entry.strip().split("/")
            if len(fields) < 5 or fields[1].lower() != "open":
                continue
            rows.append(
                {
                    "ip": ip,
                    "port": int(fields[0]),
                    "protocol": "tcp",
                    "service": fields[4],
                    "version": None,
                    "vuln_codes": [],
                }
            )
    return rows


def detect_http_banner(ip: str, port: int, use_https_hint: bool = False) -> str:
    if not REQUESTS_AVAILABLE:
        return ""

    scheme = "https" if port in {443, 8443} or use_https_hint else "http"
    url = f"{scheme}://{ip}:{port}/"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PKTScanner/1.0)"}
    try:
        response = requests.get(url, headers=headers, timeout=3, verify=False, allow_redirects=True)
    except requests.exceptions.SSLError:
        if scheme == "https":
            try:
                response = requests.get(f"http://{ip}:{port}/", headers=headers, timeout=3, verify=False, allow_redirects=True)
            except Exception:  # noqa: BLE001
                return ""
        else:
            return ""
    except Exception:  # noqa: BLE001
        return ""

    server = response.headers.get("Server") or response.headers.get("server")
    if server:
        return sanitize_field(server)
    title_match = re.search(r"<title[^>]*>(.*?)</title>", response.text or "", re.I | re.S)
    if title_match:
        return sanitize_field(title_match.group(1))
    return sanitize_field(getattr(response, "reason", "") or "")


def enrich_http_banners(records: list[dict]) -> None:
    if not REQUESTS_AVAILABLE:
        return

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {}
        for record in records:
            service = (record.get("service") or "").lower()
            port = int(record.get("port") or 0)
            is_web = "http" in service or port in HTTP_PORTS
            if not is_web:
                continue
            future = executor.submit(detect_http_banner, record["ip"], port, "https" in service or port in {443, 8443})
            future_map[future] = record

        for future in as_completed(future_map):
            record = future_map[future]
            try:
                banner = future.result()
            except Exception:  # noqa: BLE001
                banner = ""
            if banner:
                record["version"] = f"{record['version']};{banner}" if record.get("version") else banner


def dedupe_records(records: list[dict]) -> list[dict]:
    merged: dict[tuple[str, int, str], dict] = {}
    for record in records:
        key = (record["ip"], int(record["port"]), record.get("protocol") or "tcp")
        existing = merged.get(key)
        if existing is None:
            merged[key] = dict(record)
            continue
        if not existing.get("service") and record.get("service"):
            existing["service"] = record["service"]
        if not existing.get("version") and record.get("version"):
            existing["version"] = record["version"]
        for vuln_code in record.get("vuln_codes") or []:
            if vuln_code not in existing["vuln_codes"]:
                existing["vuln_codes"].append(vuln_code)
    return sorted(merged.values(), key=lambda item: (tuple(int(part) for part in item["ip"].split(".")), item["port"]))


def build_success_payload(output_dir: Path, records: list[dict], warnings: list[str], live_hosts: list[str]) -> dict:
    return {
        "result_code": RESULT_SUCCESS,
        "message": "PKT scanning completed successfully.",
        "output_dir": str(output_dir),
        "folder_name": output_dir.name,
        "file_inventory": [name for name in OUTPUT_FILES if (output_dir / name).exists()],
        "live_hosts": live_hosts,
        "warnings": warnings,
        "scan_results": records,
        "total_records": len(records),
    }


def build_error_payload(result_code: int, message: str, output_dir: Path | None = None, warnings: list[str] | None = None) -> dict:
    return {
        "result_code": result_code,
        "message": message,
        "output_dir": str(output_dir) if output_dir else None,
        "folder_name": output_dir.name if output_dir else None,
        "warnings": warnings or [],
        "scan_results": [],
        "total_records": 0,
    }


def main() -> int:
    args = parse_args()
    warnings: list[str] = []
    output_dir: Path | None = None

    try:
        targets = load_targets(args)
        if not targets:
            print(json.dumps(build_error_payload(RESULT_INVALID_INPUT, "Không có IP/dải IP hợp lệ để scan."), ensure_ascii=False))
            return 0

        if shutil.which("nmap") is None:
            print(json.dumps(build_error_payload(RESULT_MISSING_TOOL, "Không tìm thấy công cụ nmap trên agent."), ensure_ascii=False))
            return 0

        try:
            output_dir = ensure_output_dir(args.folder_name, args.output_root)
        except Exception as exc:  # noqa: BLE001
            print(json.dumps(build_error_payload(RESULT_OUTPUT_DIR_ERROR, f"Không thể tạo thư mục output: {exc}"), ensure_ascii=False))
            return 0

        targets_file = write_targets_file(output_dir, targets)
        discovery_gnmap = output_dir / "discovery.gnmap"
        fallback_gnmap = output_dir / "fallback.gnmap"
        alive_a_file = output_dir / "alive_a.txt"
        alive_b_file = output_dir / "alive_b.txt"
        hosts_file = output_dir / "hosts.txt"
        tcp_prefix = output_dir / "tcp_full"
        udp_prefix = output_dir / "udpcore"

        tcp_scan_mode = "-sS" if getattr(os, "geteuid", lambda: 1)() == 0 else "-sT"
        if tcp_scan_mode == "-sT":
            warnings.append("Agent không chạy với quyền root, TCP scan dùng -sT thay vì -sS.")

        discovery_command = [
            "nmap", "-vv", "-sn", "-n", "-T3", "-PE", "-PP",
            f"-PS{TCP_DISCOVERY_SYN_PORTS}", "-PA80,443", f"-PU{UDP_CORE_PORTS}",
            "-iL", str(targets_file), "-oG", str(discovery_gnmap),
        ]
        fallback_command = [
            "nmap", "-vv", "-Pn", "-n", tcp_scan_mode, "-T3", "--top-ports", "200",
            "--open", "-iL", str(targets_file), "-oG", str(fallback_gnmap),
        ]
        tcp_full_command = [
            "nmap", "-vv", "-n", tcp_scan_mode, "-T3", "-p-", "-sV", "--version-intensity", "7", "--open",
            "--script", "vuln and not (http-slowloris-check or intrusive or dos or brute or malware or ssl-dh-params)",
            "--script-timeout", "30s", "-iL", str(hosts_file), "-oA", str(tcp_prefix),
        ]
        udp_core_command = [
            "nmap", "-vv", "-n", "-sU", "-T3", f"-p{UDP_CORE_PORTS}", "-sV", "--version-intensity", "7", "--open",
            "--script", "vuln and not (http-slowloris-check or intrusive or dos or brute or malware or ssl-dh-params)",
            "--script-timeout", "30s", "-iL", str(hosts_file), "-oA", str(udp_prefix),
        ]

        for command in [discovery_command, fallback_command]:
            return_code, merged_output = run_command(command, output_dir)
            if return_code != 0:
                print(json.dumps(build_error_payload(RESULT_SCAN_COMMAND_FAILED, merged_output or "Lệnh quét host discovery thất bại.", output_dir, warnings), ensure_ascii=False))
                return 0

        alive_a = parse_alive_from_discovery(discovery_gnmap)
        alive_b = parse_alive_from_fallback(fallback_gnmap)
        alive_a_file.write_text("\n".join(alive_a) + ("\n" if alive_a else ""), encoding="utf-8")
        alive_b_file.write_text("\n".join(alive_b) + ("\n" if alive_b else ""), encoding="utf-8")

        merged_hosts = []
        seen_hosts = set()
        for host in [*alive_a, *alive_b]:
            if host not in seen_hosts:
                seen_hosts.add(host)
                merged_hosts.append(host)
        hosts_file.write_text("\n".join(merged_hosts) + ("\n" if merged_hosts else ""), encoding="utf-8")

        if merged_hosts:
            for command in [tcp_full_command, udp_core_command]:
                return_code, merged_output = run_command(command, output_dir)
                if return_code != 0:
                    print(json.dumps(build_error_payload(RESULT_SCAN_COMMAND_FAILED, merged_output or "Lệnh quét TCP/UDP thất bại.", output_dir, warnings), ensure_ascii=False))
                    return 0
        else:
            warnings.append("Không phát hiện host alive; sẽ trả về kết quả rỗng để server tạo placeholder cho target.")

        try:
            records = parse_nmap_xml(output_dir / "tcp_full.xml")
            records.extend(parse_nmap_xml(output_dir / "udpcore.xml"))
            if not records:
                records.extend(parse_gnmap(output_dir / "tcp_full.gnmap"))
                records.extend(parse_gnmap(output_dir / "udpcore.gnmap"))
            enrich_http_banners(records)
            records = dedupe_records(records)
        except Exception as exc:  # noqa: BLE001
            print(json.dumps(build_error_payload(RESULT_PARSE_FAILED, f"Không thể parse kết quả scan: {exc}", output_dir, warnings), ensure_ascii=False))
            return 0

        print(json.dumps(build_success_payload(output_dir, records, warnings, merged_hosts), ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps(build_error_payload(RESULT_UNKNOWN_ERROR, f"Lỗi không xác định: {exc}", output_dir, warnings), ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
