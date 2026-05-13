from __future__ import annotations

import asyncio
import json
import shlex
import sys
from pathlib import Path
from urllib.parse import urlsplit

from app.config import Settings
from app.schemas import ExecuteRequest

PKT_SCANNING_TASK_CODE = "TASK-PKT-SCANNING"


def _normalize_nmap_target(value: str) -> str:
    compact = str(value or "").strip()
    if not compact:
        return compact
    parsed = urlsplit(compact if "://" in compact else f"//{compact}")
    if parsed.hostname:
        return parsed.hostname
    return compact


def _build_command(payload: ExecuteRequest, settings: Settings) -> list[str]:
    command = [settings.nmap_bin, "-oX", "-"]
    input_data = payload.input_data or {}

    ports = input_data.get("ports")
    if ports:
        command.extend(["-p", str(ports)])

    timing = input_data.get("timing")
    if timing:
        command.append(f"-{timing}")

    extra_args = input_data.get("extra_args")
    if isinstance(extra_args, list):
        command.extend(str(item) for item in extra_args if item)
    elif isinstance(extra_args, str) and extra_args.strip():
        command.extend(shlex.split(extra_args))

    command.append(_normalize_nmap_target(payload.target.value))
    return command


def _resolve_agent_path(path_value: str) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate
    return Path(__file__).resolve().parents[1] / candidate


def _target_entries(payload: ExecuteRequest) -> list[str]:
    input_data = payload.input_data or {}
    scan_entries = input_data.get("scan_entries")
    if isinstance(scan_entries, list):
        return [_normalize_nmap_target(str(item)) for item in scan_entries if str(item).strip()]
    if isinstance(scan_entries, str) and scan_entries.strip():
        return [_normalize_nmap_target(item) for item in scan_entries.split(",") if item.strip()]
    return [_normalize_nmap_target(payload.target.value)]


def _mock_pkt_payload(payload: ExecuteRequest, settings: Settings) -> str:
    records = []
    for target in _target_entries(payload):
        records.append(
            {
                "ip": target.split("/")[0],
                "port": 80,
                "protocol": "tcp",
                "service": "http",
                "version": "mock-nginx",
                "vuln_codes": [],
            }
        )

    output_root = _resolve_agent_path(settings.pkt_scanner_output_root)
    folder_name = (payload.input_data or {}).get("folder_name") or f"pkt-scan-{payload.task_execution_id}"
    return json.dumps(
        {
            "result_code": 200,
            "message": "PKT scanning mock completed successfully.",
            "output_dir": str(output_root / folder_name),
            "folder_name": folder_name,
            "file_inventory": [],
            "live_hosts": [item["ip"] for item in records],
            "warnings": ["NMAP_AGENT_MODE=mock, returned sample PKT scan records."],
            "scan_results": records,
            "total_records": len(records),
        },
        ensure_ascii=False,
    )


def _build_pkt_command(payload: ExecuteRequest, settings: Settings) -> list[str]:
    output_root = _resolve_agent_path(settings.pkt_scanner_output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    targets_file = output_root / f"task-execution-{payload.task_execution_id}-targets.json"
    targets_file.write_text(json.dumps(_target_entries(payload), ensure_ascii=False), encoding="utf-8")

    folder_name = (payload.input_data or {}).get("folder_name") or f"pkt-scan-{payload.task_execution_id}"
    return [
        sys.executable,
        str(_resolve_agent_path(settings.pkt_scanner_script_path)),
        "--targets-file",
        str(targets_file),
        "--folder-name",
        str(folder_name),
        "--output-root",
        str(output_root),
    ]


def _mock_xml(target_value: str) -> str:
    return f"""<nmaprun>
  <host>
    <status state="up" />
    <address addr="{target_value}" addrtype="ipv4" />
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open" />
        <service name="ssh" product="OpenSSH" version="9.0" />
      </port>
      <port protocol="tcp" portid="80">
        <state state="open" />
        <service name="http" product="nginx" version="1.24" />
      </port>
      <port protocol="tcp" portid="443">
        <state state="open" />
        <service name="https" product="nginx" version="1.24" />
      </port>
    </ports>
  </host>
</nmaprun>"""


async def run_nmap(payload: ExecuteRequest, settings: Settings) -> tuple[str, list[str]]:
    if payload.task.code == PKT_SCANNING_TASK_CODE:
        if settings.nmap_agent_mode.lower() == "mock":
            await asyncio.sleep(2)
            return _mock_pkt_payload(payload, settings), ["mock-pkt", *_target_entries(payload)]

        command = _build_pkt_command(payload, settings)
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        targets_file = Path(command[command.index("--targets-file") + 1])
        targets_file.unlink(missing_ok=True)

        output = stdout.decode("utf-8", errors="ignore").strip()
        if not output:
            output = stderr.decode("utf-8", errors="ignore").strip()
        if process.returncode != 0:
            raise RuntimeError(output or f"PKT scanner exited with code {process.returncode}")
        return output, command

    if settings.nmap_agent_mode.lower() == "mock":
        await asyncio.sleep(2)
        return _mock_xml(payload.target.value), ["mock", payload.target.value]

    command = _build_command(payload, settings)
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        error_text = stderr.decode("utf-8", errors="ignore").strip() or f"nmap exited with code {process.returncode}"
        raise RuntimeError(error_text)

    return stdout.decode("utf-8", errors="ignore"), command
