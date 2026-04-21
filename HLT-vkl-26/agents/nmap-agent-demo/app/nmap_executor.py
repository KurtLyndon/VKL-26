from __future__ import annotations

import asyncio
import shlex

from app.config import Settings
from app.schemas import ExecuteRequest


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

    command.append(payload.target.value)
    return command


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
