from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.backend_client import BackendClient
from app.config import get_settings
from app.nmap_executor import run_nmap
from app.schemas import ExecuteRequest, ExecuteResponse

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

        await backend_client.send_task_heartbeat(
            payload.callback_paths.task_heartbeat_path,
            raw_log=f"Execution finished. Preparing normalization for `{payload.target.value}`.",
            progress_percent=90,
            output_data_json={"agent_execution_id": agent_execution_id, "command": command_display},
        )

        duration_seconds = round(perf_counter() - started_perf, 3)
        await backend_client.send_task_status(
            payload.callback_paths.task_status_path,
            status="completed",
            output_data_json={
                "agent_execution_id": agent_execution_id,
                "agent_mode": settings.nmap_agent_mode,
                "command": command_display,
                "duration_seconds": duration_seconds,
                "started_at": started_at.isoformat(),
                "finished_at": datetime.now(timezone.utc).isoformat(),
            },
            raw_log=f"Nmap execution completed for target {payload.target.value}.",
        )

        if payload.target.id is not None:
            await backend_client.send_normalized_result(
                payload.callback_paths.normalize_scan_result_path,
                raw_output=raw_output,
                operation_execution_id=payload.operation_execution_id,
                task_execution_id=payload.task_execution_id,
                target_id=payload.target.id,
            )

        RUNS[agent_execution_id] = {
            "status": "completed",
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
        meta={"mode": "async-demo"},
        message="Nmap agent accepted the task and will callback the backend asynchronously.",
        agent_execution_id=agent_execution_id,
    )
