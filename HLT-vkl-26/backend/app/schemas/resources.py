from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AccountGroupBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    is_active: bool = True


class AccountGroupCreate(AccountGroupBase):
    pass


class AccountGroupUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class AccountGroupRead(AccountGroupBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class AppPermissionBase(BaseModel):
    code: str
    name: str
    module_name: str
    description: str | None = None


class AppPermissionCreate(AppPermissionBase):
    pass


class AppPermissionUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    module_name: str | None = None
    description: str | None = None


class AppPermissionRead(AppPermissionBase, ORMModel):
    id: int
    created_at: datetime


class UserAccountBase(BaseModel):
    username: str
    full_name: str
    email: str | None = None
    group_id: int | None = None
    is_active: bool = True


class UserAccountCreate(UserAccountBase):
    password: str = Field(min_length=6)


class UserAccountUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    email: str | None = None
    password: str | None = Field(default=None, min_length=6)
    group_id: int | None = None
    is_active: bool | None = None


class UserAccountRead(UserAccountBase, ORMModel):
    id: int
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserAccountRead
    permissions: list[str]


class CurrentUserResponse(BaseModel):
    user: UserAccountRead
    permissions: list[str]


class GroupPermissionItem(BaseModel):
    permission_id: int
    permission_code: str
    permission_name: str
    module_name: str
    is_enabled: bool = False


class GroupPermissionUpdateItem(BaseModel):
    permission_id: int
    is_enabled: bool


class GroupPermissionUpdateRequest(BaseModel):
    items: list[GroupPermissionUpdateItem]


class DemoMockFlowRequest(BaseModel):
    operation_id: int | None = None
    target_id: int | None = None


class DemoMockFlowResponse(BaseModel):
    operation_id: int
    operation_execution_id: int
    task_execution_ids: list[int]
    findings_created: int
    execution_status: str
    worker_summary: "WorkerRunResponse"


class AgentBase(BaseModel):
    code: str
    name: str
    agent_type: str
    host: str | None = None
    ip_address: str | None = None
    port: int | None = None
    version: str | None = None
    status: str = "offline"
    last_seen_at: datetime | None = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: str | None = None
    agent_type: str | None = None
    host: str | None = None
    ip_address: str | None = None
    port: int | None = None
    version: str | None = None
    status: str | None = None
    last_seen_at: datetime | None = None


class AgentRead(AgentBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class TaskBase(BaseModel):
    code: str
    name: str
    agent_type: str
    script_name: str | None = None
    script_path: str | None = None
    script_content: str | None = None
    input_schema_json: dict | None = None
    output_schema_json: dict | None = None
    description: str | None = None
    version: str | None = None
    is_active: bool = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: str | None = None
    agent_type: str | None = None
    script_name: str | None = None
    script_path: str | None = None
    script_content: str | None = None
    input_schema_json: dict | None = None
    output_schema_json: dict | None = None
    description: str | None = None
    version: str | None = None
    is_active: bool | None = None


class TaskRead(TaskBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class OperationBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    schedule_type: str = "none"
    schedule_config_json: dict | None = None
    is_active: bool = True


class OperationCreate(OperationBase):
    pass


class OperationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    schedule_type: str | None = None
    schedule_config_json: dict | None = None
    is_active: bool | None = None


class OperationRead(OperationBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class OperationTaskBase(BaseModel):
    operation_id: int
    task_id: int
    order_index: int = 0
    input_override_json: dict | None = None
    continue_on_error: bool = False


class OperationTaskCreate(OperationTaskBase):
    pass


class OperationTaskUpdate(BaseModel):
    task_id: int | None = None
    order_index: int | None = None
    input_override_json: dict | None = None
    continue_on_error: bool | None = None


class OperationTaskRead(OperationTaskBase, ORMModel):
    id: int
    created_at: datetime


class OperationExecutionBase(BaseModel):
    operation_id: int
    execution_code: str
    trigger_type: str = "manual"
    status: str = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary_json: dict | None = None


class OperationExecutionCreate(OperationExecutionBase):
    pass


class OperationExecutionUpdate(BaseModel):
    trigger_type: str | None = None
    status: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    summary_json: dict | None = None


class OperationExecutionRead(OperationExecutionBase, ORMModel):
    id: int
    created_at: datetime


class TaskExecutionBase(BaseModel):
    operation_execution_id: int
    operation_task_id: int
    task_id: int
    agent_id: int
    status: str = "pending"
    input_data_json: dict | None = None
    output_data_json: dict | None = None
    raw_log: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class TaskExecutionCreate(TaskExecutionBase):
    pass


class TaskExecutionUpdate(BaseModel):
    agent_id: int | None = None
    status: str | None = None
    input_data_json: dict | None = None
    output_data_json: dict | None = None
    raw_log: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class TaskExecutionRead(TaskExecutionBase, ORMModel):
    id: int


class TargetBase(BaseModel):
    code: str
    name: str
    target_type: str = "network"
    ip_range: str | None = None
    domain: str | None = None
    description: str | None = None


class TargetCreate(TargetBase):
    pass


class TargetUpdate(BaseModel):
    name: str | None = None
    target_type: str | None = None
    ip_range: str | None = None
    domain: str | None = None
    description: str | None = None


class TargetRead(TargetBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class TargetAttributeDefinitionBase(BaseModel):
    attribute_code: str
    attribute_name: str
    data_type: str = "text"
    is_required: bool = False
    default_value: str | None = None
    description: str | None = None


class TargetAttributeDefinitionCreate(TargetAttributeDefinitionBase):
    pass


class TargetAttributeDefinitionUpdate(BaseModel):
    attribute_name: str | None = None
    data_type: str | None = None
    is_required: bool | None = None
    default_value: str | None = None
    description: str | None = None


class TargetAttributeDefinitionRead(TargetAttributeDefinitionBase, ORMModel):
    id: int
    created_at: datetime


class TargetAttributeValueBase(BaseModel):
    target_id: int
    attribute_definition_id: int
    value_text: str


class TargetAttributeValueCreate(TargetAttributeValueBase):
    pass


class TargetAttributeValueUpdate(BaseModel):
    value_text: str | None = None


class TargetAttributeValueRead(TargetAttributeValueBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class TargetGroupBase(BaseModel):
    code: str
    name: str
    description: str | None = None


class TargetGroupCreate(TargetGroupBase):
    pass


class TargetGroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class TargetGroupRead(TargetGroupBase, ORMModel):
    id: int
    created_at: datetime


class VulnerabilityBase(BaseModel):
    code: str
    title: str
    level: int = Field(default=0, ge=0)
    threat: str | None = None
    proposal: str | None = None
    poc_file_name: str | None = None
    description: str | None = None


class VulnerabilityCreate(VulnerabilityBase):
    pass


class VulnerabilityUpdate(BaseModel):
    title: str | None = None
    level: int | None = Field(default=None, ge=0)
    threat: str | None = None
    proposal: str | None = None
    poc_file_name: str | None = None
    description: str | None = None


class VulnerabilityRead(VulnerabilityBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class VulnerabilityScriptBase(BaseModel):
    vulnerability_id: int
    script_name: str
    script_type: str = "py"
    script_content: str
    version: str | None = None
    is_active: bool = True


class VulnerabilityScriptCreate(VulnerabilityScriptBase):
    pass


class VulnerabilityScriptUpdate(BaseModel):
    script_name: str | None = None
    script_type: str | None = None
    script_content: str | None = None
    version: str | None = None
    is_active: bool | None = None


class VulnerabilityScriptRead(VulnerabilityScriptBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class ScanResultBase(BaseModel):
    operation_execution_id: int
    task_execution_id: int
    target_id: int
    agent_type: str
    source_tool: str | None = None
    raw_output: str | None = None
    normalized_output_json: dict | None = None
    detected_at: datetime | None = None
    parse_status: str = "success"


class ScanResultCreate(ScanResultBase):
    pass


class ScanResultUpdate(BaseModel):
    agent_type: str | None = None
    source_tool: str | None = None
    raw_output: str | None = None
    normalized_output_json: dict | None = None
    detected_at: datetime | None = None
    parse_status: str | None = None


class ScanResultRead(ScanResultBase, ORMModel):
    id: int
    created_at: datetime


class ScanResultFindingBase(BaseModel):
    scan_result_id: int
    vulnerability_id: int | None = None
    finding_code: str
    severity: str | None = None
    title: str
    description: str | None = None
    port: int | None = None
    protocol: str | None = None
    service_name: str | None = None
    evidence: str | None = None
    confidence: int | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    status: str = "open"


class ScanResultFindingCreate(ScanResultFindingBase):
    pass


class ScanResultFindingUpdate(BaseModel):
    vulnerability_id: int | None = None
    severity: str | None = None
    title: str | None = None
    description: str | None = None
    port: int | None = None
    protocol: str | None = None
    service_name: str | None = None
    evidence: str | None = None
    confidence: int | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    status: str | None = None


class ScanResultFindingRead(ScanResultFindingBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class ReportTemplateBase(BaseModel):
    code: str
    name: str
    report_type: str
    filter_config_json: dict | None = None
    layout_config_json: dict | None = None


class ReportTemplateCreate(ReportTemplateBase):
    pass


class ReportTemplateUpdate(BaseModel):
    name: str | None = None
    report_type: str | None = None
    filter_config_json: dict | None = None
    layout_config_json: dict | None = None


class ReportTemplateRead(ReportTemplateBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class GeneratedReportBase(BaseModel):
    report_template_id: int
    operation_execution_id: int | None = None
    file_name: str
    file_path: str | None = None
    generated_at: datetime | None = None
    generated_by: str | None = None
    summary_json: dict | None = None


class GeneratedReportCreate(GeneratedReportBase):
    pass


class GeneratedReportUpdate(BaseModel):
    file_name: str | None = None
    file_path: str | None = None
    generated_at: datetime | None = None
    generated_by: str | None = None
    summary_json: dict | None = None


class GeneratedReportRead(GeneratedReportBase, ORMModel):
    id: int


class ReportSnapshotBase(BaseModel):
    generated_report_id: int
    snapshot_date: datetime | None = None
    data_json: dict | None = None


class ReportSnapshotCreate(ReportSnapshotBase):
    pass


class ReportSnapshotUpdate(BaseModel):
    snapshot_date: datetime | None = None
    data_json: dict | None = None


class ReportSnapshotRead(ReportSnapshotBase, ORMModel):
    id: int
    created_at: datetime


class OperationLaunchRequest(BaseModel):
    trigger_type: str = "manual"
    shared_input: dict | None = None


class OperationLaunchResponse(BaseModel):
    execution: OperationExecutionRead
    task_executions: list[TaskExecutionRead]


class AgentHeartbeatRequest(BaseModel):
    agent_id: int | None = None
    agent_code: str | None = None
    status: str = "online"
    host: str | None = None
    ip_address: str | None = None
    port: int | None = None
    version: str | None = None
    seen_at: datetime | None = None
    metadata_json: dict | None = None

    @model_validator(mode="after")
    def validate_identifier(self) -> "AgentHeartbeatRequest":
        if self.agent_id is None and not self.agent_code:
            raise ValueError("agent_id or agent_code is required")
        return self


class AgentHeartbeatResponse(BaseModel):
    acknowledged_at: datetime
    agent: AgentRead
    metadata_json: dict | None = None


class TaskExecutionStatusRequest(BaseModel):
    status: str
    output_data_json: dict | None = None
    raw_log: str | None = None


class TaskExecutionHeartbeatRequest(BaseModel):
    agent_id: int | None = None
    agent_code: str | None = None
    status: str = "running"
    raw_log: str | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    output_data_json: dict | None = None
    seen_at: datetime | None = None


class TaskExecutionHeartbeatResponse(BaseModel):
    acknowledged_at: datetime
    operation_execution: OperationExecutionRead
    task_execution: TaskExecutionRead


class AgentExecuteTaskDescriptor(BaseModel):
    id: int
    code: str
    name: str
    agent_type: str
    script_name: str | None = None
    script_path: str | None = None
    version: str | None = None


class AgentExecuteAgentDescriptor(BaseModel):
    id: int
    code: str
    name: str
    agent_type: str
    version: str | None = None


class AgentExecuteTargetDescriptor(BaseModel):
    id: int | None = None
    name: str | None = None
    target_type: str | None = None
    value: str
    ip_range: str | None = None
    domain: str | None = None


class AgentExecuteCallbacks(BaseModel):
    agent_heartbeat_path: str
    task_heartbeat_path: str
    task_status_path: str
    normalize_scan_result_path: str


class AgentExecuteRequest(BaseModel):
    contract_version: str
    dispatched_at: datetime
    task_execution_id: int
    operation_execution_id: int
    agent: AgentExecuteAgentDescriptor
    task: AgentExecuteTaskDescriptor
    target: AgentExecuteTargetDescriptor
    input_data: dict = Field(default_factory=dict)
    callback_paths: AgentExecuteCallbacks


class AgentExecuteResponse(BaseModel):
    contract_version: str
    status: str = "completed"
    accepted: bool = True
    raw_output: str | None = None
    output_data: dict | None = None
    meta: dict | None = None
    message: str | None = None
    agent_execution_id: str | None = None


class AgentExecuteContractDocument(BaseModel):
    contract_version: str
    execute_path: str
    heartbeat_paths: list[str]
    completion_path: str
    normalize_path: str
    notes: list[str]
    execute_request_example: AgentExecuteRequest
    execute_response_examples: list[AgentExecuteResponse]


class OperationRuntimeOverviewItem(BaseModel):
    operation_id: int
    operation_code: str
    operation_name: str
    total_executions: int
    latest_execution_id: int | None = None
    latest_execution_status: str | None = None
    queued_tasks: int = 0
    running_tasks: int = 0
    failed_tasks: int = 0
    completed_tasks: int = 0


class SchedulerRunResponse(BaseModel):
    checked_operations: int
    launched_operations: int
    launched_execution_ids: list[int]
    run_started_at: datetime


class WorkerRunResponse(BaseModel):
    checked_executions: int
    processed_tasks: int
    completed_tasks: int
    failed_tasks: int
    canceled_tasks: int
    processed_execution_ids: list[int]
    run_started_at: datetime


class OperationResultExchangeBase(BaseModel):
    operation_id: int
    action_type: str
    file_name: str
    file_path: str | None = None
    file_format: str
    status: str = "pending"
    executed_at: datetime | None = None
    note: str | None = None


class OperationResultExchangeCreate(OperationResultExchangeBase):
    pass


class OperationResultExchangeUpdate(BaseModel):
    file_name: str | None = None
    file_path: str | None = None
    file_format: str | None = None
    status: str | None = None
    executed_at: datetime | None = None
    note: str | None = None


class OperationResultExchangeRead(OperationResultExchangeBase, ORMModel):
    id: int


class OperationResultExportRequest(BaseModel):
    file_format: str = "json"


class OperationResultExportResponse(BaseModel):
    history: OperationResultExchangeRead
    exported_records: int


class OperationResultImportRequest(BaseModel):
    payload_json: dict


class OperationResultImportResponse(BaseModel):
    history: OperationResultExchangeRead
    imported_scan_results: int
    imported_findings: int


class ParserNormalizeRequest(BaseModel):
    agent_type: str
    source_tool: str | None = None
    raw_output: str
    operation_execution_id: int
    task_execution_id: int
    target_id: int
    detected_at: datetime | None = None


class ParserNormalizeResponse(BaseModel):
    scan_result: ScanResultRead
    findings: list[ScanResultFindingRead]


class DashboardSummary(BaseModel):
    agents: int
    tasks: int
    operations: int
    operation_executions: int
    task_executions: int
    targets: int
    vulnerabilities: int
    scan_results: int
    open_findings: int
    report_templates: int
    generated_reports: int


DemoMockFlowResponse.model_rebuild()
