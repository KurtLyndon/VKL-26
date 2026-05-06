from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from app.models import TaskExecution
from app.services.agents.runner_base import AgentRunner
from app.services.poc_repository import DATA_DIR


class NmapRunner(AgentRunner):
    agent_type = "nmap"

    def run(self, task_execution: TaskExecution, target_value: str) -> str:
        if task_execution.task.code == "TASK-PKT-SCANNING":
            return self._run_pkt_scanning(task_execution)

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
    </ports>
  </host>
</nmaprun>"""

    def _run_pkt_scanning(self, task_execution: TaskExecution) -> str:
        input_data = task_execution.input_data_json or {}
        scan_entries = input_data.get("scan_entries") or []
        folder_name = input_data.get("folder_name") or f"pkt-scan-{task_execution.id}"
        script_path = self._resolve_script_path(task_execution.task.script_path)
        runs_root = DATA_DIR / "agent_runs" / "nmap"
        runs_root.mkdir(parents=True, exist_ok=True)
        targets_file = runs_root / f"task-execution-{task_execution.id}-targets.json"
        targets_file.write_text(json.dumps(scan_entries, ensure_ascii=False), encoding="utf-8")

        if not script_path.exists():
            raise RuntimeError(f"Không tìm thấy script PKT scanner tại {script_path}")

        command = [
            sys.executable,
            str(script_path),
            "--targets-file",
            str(targets_file),
            "--folder-name",
            str(folder_name),
            "--output-root",
            str(runs_root),
        ]

        try:
            result = subprocess.run(command, capture_output=True, text=True)
        finally:
            targets_file.unlink(missing_ok=True)

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if not stdout:
            raise RuntimeError(stderr or "PKT scanner không trả dữ liệu đầu ra.")
        return stdout

    @staticmethod
    def _resolve_script_path(script_path: str | None) -> Path:
        if not script_path:
            return DATA_DIR / "agent_task_scripts" / "nmap" / "pkt_scannerv1.py"

        candidate = Path(script_path)
        if candidate.is_absolute():
            return candidate

        normalized = script_path.replace("\\", "/").lstrip("./")
        return DATA_DIR.parent / normalized
