from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Agent, OperationExecution, Target, TaskExecution
from app.schemas.resources import (
    AgentExecuteAgentDescriptor,
    AgentExecuteCallbacks,
    AgentExecuteContractDocument,
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentExecuteTargetDescriptor,
    AgentExecuteTaskDescriptor,
    AgentHeartbeatRequest,
    TaskExecutionHeartbeatRequest,
)
from app.services.execution import refresh_operation_execution_summary

AGENT_EXECUTE_CONTRACT_VERSION = "2026-04-21"


def _resolve_agent(db: Session, *, agent_id: int | None, agent_code: str | None) -> Agent:
    agent = db.get(Agent, agent_id) if agent_id is not None else None
    if agent is None and agent_code:
        agent = db.query(Agent).filter(Agent.code == agent_code).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


def update_agent_heartbeat(db: Session, payload: AgentHeartbeatRequest) -> tuple[Agent, datetime]:
    agent = _resolve_agent(db, agent_id=payload.agent_id, agent_code=payload.agent_code)
    acknowledged_at = payload.seen_at or datetime.utcnow()

    if payload.host is not None:
        agent.host = payload.host
    if payload.ip_address is not None:
        agent.ip_address = payload.ip_address
    if payload.port is not None:
        agent.port = payload.port
    if payload.version is not None:
        agent.version = payload.version

    agent.status = payload.status or "online"
    agent.last_seen_at = acknowledged_at

    db.commit()
    db.refresh(agent)
    return agent, acknowledged_at


def update_task_execution_heartbeat(
    db: Session, task_execution_id: int, payload: TaskExecutionHeartbeatRequest
) -> tuple[TaskExecution, OperationExecution, datetime]:
    task_execution = db.get(TaskExecution, task_execution_id)
    if not task_execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task execution not found")

    if payload.agent_id is not None and task_execution.agent_id != payload.agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task execution does not belong to this agent")

    if payload.agent_code:
        agent = _resolve_agent(db, agent_id=task_execution.agent_id, agent_code=payload.agent_code)
        if agent.id != task_execution.agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task execution does not belong to this agent",
            )

    if task_execution.status in {"completed", "failed", "canceled"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task execution is already finished")

    acknowledged_at = payload.seen_at or datetime.utcnow()

    agent = db.get(Agent, task_execution.agent_id)
    if agent:
        agent.status = "online"
        agent.last_seen_at = acknowledged_at

    next_status = payload.status or "running"
    if next_status not in {"queued", "running"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Heartbeat status must be queued or running",
        )

    task_execution.status = next_status
    if task_execution.started_at is None:
        task_execution.started_at = acknowledged_at

    merged_output = dict(task_execution.output_data_json or {})
    if payload.output_data_json:
        merged_output.update(payload.output_data_json)
    if payload.progress_percent is not None:
        merged_output["progress_percent"] = payload.progress_percent
    if merged_output:
        task_execution.output_data_json = merged_output
    if payload.raw_log is not None:
        task_execution.raw_log = payload.raw_log

    operation_execution = refresh_operation_execution_summary(db, task_execution.operation_execution_id, acknowledged_at)
    db.commit()
    db.refresh(task_execution)
    db.refresh(operation_execution)
    return task_execution, operation_execution, acknowledged_at


def build_execute_request(agent: Agent, task_execution: TaskExecution, target: Target | None, target_value: str) -> AgentExecuteRequest:
    return AgentExecuteRequest(
        contract_version=AGENT_EXECUTE_CONTRACT_VERSION,
        dispatched_at=datetime.utcnow(),
        task_execution_id=task_execution.id,
        operation_execution_id=task_execution.operation_execution_id,
        agent=AgentExecuteAgentDescriptor(
            id=agent.id,
            code=agent.code,
            name=agent.name,
            agent_type=agent.agent_type,
            version=agent.version,
        ),
        task=AgentExecuteTaskDescriptor(
            id=task_execution.task.id,
            code=task_execution.task.code,
            name=task_execution.task.name,
            agent_type=task_execution.task.agent_type,
            script_name=task_execution.task.script_name,
            script_path=task_execution.task.script_path,
            version=task_execution.task.version,
        ),
        target=AgentExecuteTargetDescriptor(
            id=target.id if target else None,
            name=target.name if target else None,
            target_type=target.target_type if target else None,
            value=target_value,
            ip_range=target.ip_range if target else None,
            domain=target.domain if target else None,
        ),
        input_data=task_execution.input_data_json or {},
        callback_paths=AgentExecuteCallbacks(
            agent_heartbeat_path="/api/v1/agents/heartbeat",
            task_heartbeat_path=f"/api/v1/task-executions/{task_execution.id}/heartbeat",
            task_status_path=f"/api/v1/task-executions/{task_execution.id}/status",
            normalize_scan_result_path="/api/v1/scan-results/normalize",
        ),
    )


def parse_execute_response(response_json: dict) -> tuple[str | None, dict, dict]:
    raw_output = response_json.get("raw_output")
    output_data = response_json.get("output_data") or {}
    meta = dict(response_json.get("meta") or {})
    if response_json.get("message"):
        meta["message"] = response_json["message"]
    if response_json.get("agent_execution_id"):
        meta["agent_execution_id"] = response_json["agent_execution_id"]
    if response_json.get("contract_version"):
        meta["contract_version"] = response_json["contract_version"]
    return raw_output, output_data | {"dispatch_status": response_json.get("status", "completed")}, meta


def get_execute_contract_document() -> AgentExecuteContractDocument:
    example_request = AgentExecuteRequest(
        contract_version=AGENT_EXECUTE_CONTRACT_VERSION,
        dispatched_at=datetime(2026, 4, 21, 11, 30, 0),
        task_execution_id=101,
        operation_execution_id=55,
        agent=AgentExecuteAgentDescriptor(
            id=7,
            code="nmap-agent-01",
            name="Nmap Agent 01",
            agent_type="nmap",
            version="1.2.0",
        ),
        task=AgentExecuteTaskDescriptor(
            id=12,
            code="PORT_SCAN",
            name="Port Scan",
            agent_type="nmap",
            script_name="scan.py",
            script_path="agents/nmap/scan.py",
            version="2026.04",
        ),
        target=AgentExecuteTargetDescriptor(
            id=3,
            name="Internal Gateway",
            target_type="network",
            value="10.10.1.1",
            ip_range="10.10.1.1",
            domain=None,
        ),
        input_data={"ports": "1-1024", "timing": "T4"},
        callback_paths=AgentExecuteCallbacks(
            agent_heartbeat_path="/api/v1/agents/heartbeat",
            task_heartbeat_path="/api/v1/task-executions/101/heartbeat",
            task_status_path="/api/v1/task-executions/101/status",
            normalize_scan_result_path="/api/v1/scan-results/normalize",
        ),
    )

    return AgentExecuteContractDocument(
        contract_version=AGENT_EXECUTE_CONTRACT_VERSION,
        execute_path="/execute",
        heartbeat_paths=[
            "/api/v1/agents/heartbeat",
            "/api/v1/task-executions/{task_execution_id}/heartbeat",
        ],
        completion_path="/api/v1/task-executions/{task_execution_id}/status",
        normalize_path="/api/v1/scan-results/normalize",
        notes=[
            "External agents may complete synchronously by returning status=completed with raw_output.",
            "External agents may acknowledge asynchronously with status=accepted or status=running, then use heartbeat and status callbacks.",
            "Heartbeat callbacks refresh agent.last_seen_at and can attach progress_percent or partial output_data_json.",
            "Task completion should still be reported through the task status endpoint, optionally followed by scan normalization.",
        ],
        execute_request_example=example_request,
        execute_response_examples=[
            AgentExecuteResponse(
                contract_version=AGENT_EXECUTE_CONTRACT_VERSION,
                status="completed",
                accepted=True,
                raw_output='{"hosts":[{"ip":"10.10.1.1","ports":[80,443]}]}',
                output_data={"engine": "nmap", "duration_seconds": 12},
                meta={"mode": "sync"},
                message="Execution completed inline.",
                agent_execution_id="agent-run-101",
            ),
            AgentExecuteResponse(
                contract_version=AGENT_EXECUTE_CONTRACT_VERSION,
                status="accepted",
                accepted=True,
                raw_output=None,
                output_data={"queue_position": 1},
                meta={"mode": "async"},
                message="Execution accepted; progress will be reported via heartbeat callbacks.",
                agent_execution_id="agent-run-102",
            ),
        ],
    )
