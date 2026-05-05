#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

COMMUNITY_STRINGS = [
    "cisco",
    "public",
    "private",
]

OID_SYSTEM_INFO = ".1.3.6.1.2.1.1.1"
OID_INTERFACE_NAME = ".1.3.6.1.2.1.2.2.1.2"
OID_IP_ADDRESS = ".1.3.6.1.2.1.4.20.1.1"
OID_ALIAS = ".1.3.6.1.2.1.31.1.1.1.18"
COMMAND_TIMEOUT = 8


def _target_ip() -> str | None:
    return (os.getenv("HLT_TARGET_IP") or "").strip() or None


def _output_file_path() -> Path:
    if len(sys.argv) != 2:
        raise ValueError("Thiếu tên file PoC đầu ra.")
    output_name = sys.argv[1].strip()
    if not output_name:
        raise ValueError("Tên file PoC đầu ra đang trống.")
    return Path.cwd() / output_name


def run_snmpwalk(target: str, community: str, oid: str) -> tuple[bool, list[str], str]:
    snmpwalk_bin = shutil.which("snmpwalk")
    if snmpwalk_bin is None:
        return False, [], "missing-snmpwalk"

    command = [
        snmpwalk_bin,
        "-v",
        "2c",
        "-c",
        community,
        "-Oqv",
        target,
        oid,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, [], "timeout"
    except Exception as exc:  # noqa: BLE001
        return False, [], f"exception:{exc}"

    stdout_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if result.returncode != 0:
        return False, stdout_lines, result.stderr.strip() or f"return-code:{result.returncode}"
    if not stdout_lines:
        return False, [], "no-data"
    return True, stdout_lines, ""


def collect_snmp_data(target: str, community: str) -> dict:
    sys_ok, sys_info_raw, sys_err = run_snmpwalk(target, community, OID_SYSTEM_INFO)
    names_ok, names, names_err = run_snmpwalk(target, community, OID_INTERFACE_NAME)
    ips_ok, ips, ips_err = run_snmpwalk(target, community, OID_IP_ADDRESS)
    aliases_ok, aliases, aliases_err = run_snmpwalk(target, community, OID_ALIAS)

    has_data = any(
        [
            sys_ok and bool(sys_info_raw),
            names_ok and bool(names),
            ips_ok and bool(ips),
            aliases_ok and bool(aliases),
        ]
    )

    errors: list[str] = []
    for label, ok, err in [
        ("System Info", sys_ok, sys_err),
        ("Interface Name", names_ok, names_err),
        ("IP Address", ips_ok, ips_err),
        ("Alias", aliases_ok, aliases_err),
    ]:
        if not ok and err:
            errors.append(f"{label}: {err}")

    return {
        "community": community,
        "has_data": has_data,
        "system_info": sys_info_raw[0] if sys_info_raw else "N/A",
        "names": names,
        "ips": ips,
        "aliases": aliases,
        "errors": errors,
    }


def render_report(target: str, results: list[dict]) -> str:
    lines = []
    lines.append("=" * 100)
    lines.append("SNMP VULNERABILITY VERIFICATION REPORT")
    lines.append("=" * 100)
    lines.append(f"Target: {target}")
    lines.append(f"Community strings checked: {len(COMMUNITY_STRINGS)}")

    for result in results:
        lines.append("")
        lines.append("=" * 100)
        lines.append(f"COMMUNITY STRING: {result['community']}")
        lines.append("=" * 100)

        if not result["has_data"]:
            lines.append(f"[NO DATA] Community '{result['community']}' did not return SNMP data.")
            for error_message in result["errors"]:
                lines.append(f"- {error_message}")
            continue

        lines.append(f"[DATA FOUND] Community '{result['community']}' returned SNMP data.")
        lines.append(f"System: {result['system_info']}")
        lines.append("-" * 100)
        lines.append(f"{'Interface':<35} | {'IP Address':<20} | {'Alias':<35}")
        lines.append("-" * 100)

        names = result["names"]
        ips = result["ips"]
        aliases = result["aliases"]
        max_len = max(len(names), len(ips), len(aliases))
        if max_len == 0:
            lines.append("No interface/ip/alias rows returned, but SNMP system data is accessible.")
        else:
            for index in range(max_len):
                name = names[index] if index < len(names) else "N/A"
                ip = ips[index] if index < len(ips) else "N/A"
                alias = aliases[index] if index < len(aliases) else ""
                lines.append(f"{name:<35} | {ip:<20} | {alias:<35}")

        if result["errors"]:
            lines.append("-" * 100)
            lines.append("Partial OID failures:")
            for error_message in result["errors"]:
                lines.append(f"- {error_message}")

    lines.append("")
    lines.append("=" * 100)
    lines.append("END OF REPORT")
    lines.append("=" * 100)
    return "\n".join(lines) + "\n"


def main() -> int:
    try:
        output_file_path = _output_file_path()
    except ValueError:
        return 500

    target = _target_ip()
    if not target:
        return 500

    if shutil.which("snmpwalk") is None:
        return 502

    try:
        results = [collect_snmp_data(target, community) for community in COMMUNITY_STRINGS]
        any_success = any(item["has_data"] for item in results)

        if not any_success:
            return 201

        output_file_path.write_text(render_report(target, results), encoding="utf-8")
        return 200
    except ImportError:
        return 501
    except Exception:
        return 500


if __name__ == "__main__":
    raise SystemExit(main())
