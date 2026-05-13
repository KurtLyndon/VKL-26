from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.backend_client import BackendClient
from app.config import get_settings
from app.nmap_executor import run_nmap
from app.schemas import ExecuteRequest, ExecuteResponse

PKT_SCANNING_TASK_CODE = "TASK-PKT-SCANNING"

settings = get_settings()
backend_client = BackendClient(settings)
app = FastAPI(title=settings.agent_app_name)

RUNS: dict[str, dict] = {}


async def _run_execution(agent_execution_id: str, payload: ExecuteRequest) -> None:
    started_at = datetime.now(timezone.utc)
    started_perf = perf_counter()
    command_display = ""

    try:
        await backend_client.send_agent_heartbeat(
            {
                "mode": settings.nmap_agent_mode,
                "agent_execution_id": agent_execution_id,
                "task_execution_id": payload.task_execution_id,
            }
        )
        await backend_client.send_task_heartbeat(
            payload.callback_paths.task_heartbeat_path,
            raw_log="Nmap agent accepted task and is starting execution.",
            progress_percent=10,
            output_data_json={"agent_execution_id": agent_execution_id},
        )

        raw_output, command = await run_nmap(payload, settings)
        command_display = " ".join(command)

        is_pkt_scanning = payload.task.code == PKT_SCANNING_TASK_CODE
        await backend_client.send_task_heartbeat(
            payload.callback_paths.task_heartbeat_path,
            raw_log=f"Execution finished. Preparing result callback for `{payload.target.value}`.",
            progress_percent=90,
            output_data_json={"agent_execution_id": agent_execution_id, "command": command_display},
        )

        duration_seconds = round(perf_counter() - started_perf, 3)
        output_data = {
            "agent_execution_id": agent_execution_id,
            "agent_mode": settings.nmap_agent_mode,
            "command": command_display,
            "duration_seconds": duration_seconds,
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        completion_status = "completed"
        raw_log = f"Nmap execution completed for target {payload.target.value}."
        if is_pkt_scanning:
            pkt_payload = json.loads(raw_output)
            result_code = int(pkt_payload.get("result_code") or 500)
            output_data.update(
                {
                    "result_code": result_code,
                    "folder_name": pkt_payload.get("folder_name"),
                    "total_records": pkt_payload.get("total_records"),
                    "warnings": pkt_payload.get("warnings") or [],
                }
            )
            if result_code != 200:
                completion_status = "failed"
                raw_log = pkt_payload.get("message") or f"PKT scanner failed with code {result_code}."

        await backend_client.send_task_status(
            payload.callback_paths.task_status_path,
            status=completion_status,
            output_data_json=output_data,
            raw_log=raw_log,
            raw_output=raw_output if is_pkt_scanning else None,
        )

        if payload.target.id is not None and not is_pkt_scanning and completion_status == "completed":
            await backend_client.send_normalized_result(
                payload.callback_paths.normalize_scan_result_path,
                raw_output=raw_output,
                operation_execution_id=payload.operation_execution_id,
                task_execution_id=payload.task_execution_id,
                target_id=payload.target.id,
            )

        RUNS[agent_execution_id] = {
            "status": completion_status,
            "task_execution_id": payload.task_execution_id,
            "target": payload.target.value,
            "command": command_display,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:  # noqa: BLE001
        await backend_client.send_task_status(
            payload.callback_paths.task_status_path,
            status="failed",
            output_data_json={
                "agent_execution_id": agent_execution_id,
                "agent_mode": settings.nmap_agent_mode,
                "command": command_display,
            },
            raw_log=f"Nmap agent failed: {exc}",
        )
        RUNS[agent_execution_id] = {
            "status": "failed",
            "task_execution_id": payload.task_execution_id,
            "target": payload.target.value,
            "command": command_display,
            "error": str(exc),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }


@app.on_event("startup")
async def startup_event() -> None:
    try:
        await backend_client.send_agent_heartbeat({"startup": True, "mode": settings.nmap_agent_mode})
    except Exception:
        pass


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "agent_code": settings.agent_code,
        "agent_mode": settings.nmap_agent_mode,
        "backend_base_url": settings.normalized_backend_base_url,
        "supported_tasks": ["TASK-NMAP-TCP", "TASK-PKT-SCANNING"],
    }


@app.get("/runs")
def list_runs() -> dict:
    return {"items": RUNS}


@app.post("/execute", response_model=ExecuteResponse)
async def execute(payload: ExecuteRequest) -> ExecuteResponse:
    if payload.task.agent_type != "nmap":
        raise HTTPException(status_code=400, detail="This agent only supports task.agent_type = nmap")

    agent_execution_id = f"nmap-{uuid4().hex[:12]}"
    RUNS[agent_execution_id] = {
        "status": "accepted",
        "task_execution_id": payload.task_execution_id,
        "target": payload.target.value,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }

    asyncio.create_task(_run_execution(agent_execution_id, payload))
    return ExecuteResponse(
        contract_version=payload.contract_version,
        status="accepted",
        accepted=True,
        output_data={"queue_position": 1, "agent_mode": settings.nmap_agent_mode},
        meta={"mode": "async-agent"},
        message="Nmap agent accepted the task and will callback the backend asynchronously.",
        agent_execution_id=agent_execution_id,
    )
