from datetime import datetime

from pydantic import BaseModel, Field


class ExecuteAgentDescriptor(BaseModel):
    id: int
    code: str
    name: str
    agent_type: str
    version: str | None = None


class ExecuteTaskDescriptor(BaseModel):
    id: int
    code: str
    name: str
    agent_type: str
    script_name: str | None = None
    script_path: str | None = None
    version: str | None = None


class ExecuteTargetDescriptor(BaseModel):
    id: int | None = None
    name: str | None = None
    target_type: str | None = None
    value: str
    ip_range: str | None = None
    domain: str | None = None


class ExecuteCallbacks(BaseModel):
    agent_heartbeat_path: str
    task_heartbeat_path: str
    task_status_path: str
    normalize_scan_result_path: str


class ExecuteRequest(BaseModel):
    contract_version: str
    dispatched_at: datetime
    task_execution_id: int
    operation_execution_id: int
    agent: ExecuteAgentDescriptor
    task: ExecuteTaskDescriptor
    target: ExecuteTargetDescriptor
    input_data: dict = Field(default_factory=dict)
    callback_paths: ExecuteCallbacks


class ExecuteResponse(BaseModel):
    contract_version: str
    status: str = "accepted"
    accepted: bool = True
    raw_output: str | None = None
    output_data: dict | None = None
    meta: dict | None = None
    message: str | None = None
    agent_execution_id: str | None = None


class AgentHeartbeatPayload(BaseModel):
    agent_id: int | None = None
    agent_code: str | None = None
    status: str = "online"
    host: str | None = None
    ip_address: str | None = None
    port: int | None = None
    version: str | None = None
    seen_at: datetime | None = None
    metadata_json: dict | None = None


class TaskHeartbeatPayload(BaseModel):
    agent_id: int | None = None
    agent_code: str | None = None
    status: str = "running"
    raw_log: str | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    output_data_json: dict | None = None
    seen_at: datetime | None = None


class TaskStatusPayload(BaseModel):
    status: str
    output_data_json: dict | None = None
    raw_log: str | None = None
    raw_output: str | None = None


class NormalizePayload(BaseModel):
    agent_type: str
    source_tool: str | None = None
    raw_output: str
    operation_execution_id: int
    task_execution_id: int
    target_id: int
    detected_at: datetime | None = None
