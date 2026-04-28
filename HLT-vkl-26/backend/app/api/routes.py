from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import get_db
from app.models import (
    AccountGroup,
    AccountGroupPermission,
    Agent,
    GeneratedReport,
    Operation,
    OperationExecution,
    OperationResultImportExport,
    OperationTask,
    AppPermission,
    ReportTemplate,
    ReportSnapshot,
    ScanResult,
    ScanResultFinding,
    Target,
    TargetAttributeDefinition,
    TargetAttributeValue,
    TargetGroup,
    TargetGroupMapping,
    Task,
    TaskExecution,
    UserAccount,
    Vulnerability,
    VulnerabilityScript,
)
from app.schemas.resources import (
    AccountGroupCreate,
    AccountGroupRead,
    AccountGroupUpdate,
    AgentExecuteContractDocument,
    AgentCreate,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentRead,
    AgentUpdate,
    AppPermissionCreate,
    AppPermissionRead,
    AppPermissionUpdate,
    CurrentUserResponse,
    DashboardSummary,
    DemoMockFlowRequest,
    DemoMockFlowResponse,
    GeneratedReportCreate,
    GeneratedReportRead,
    GeneratedReportUpdate,
    GroupPermissionItem,
    GroupPermissionUpdateRequest,
    OperationCreate,
    OperationExecutionCreate,
    OperationExecutionRead,
    OperationExecutionUpdate,
    OperationLaunchRequest,
    OperationLaunchResponse,
    OperationRead,
    OperationResultExchangeCreate,
    OperationResultExchangeRead,
    OperationResultExchangeUpdate,
    OperationResultExportRequest,
    OperationResultExportResponse,
    OperationResultImportRequest,
    OperationResultImportResponse,
    OperationRuntimeOverviewItem,
    OperationTaskCreate,
    OperationTaskRead,
    OperationTaskUpdate,
    OperationUpdate,
    ParserNormalizeRequest,
    ParserNormalizeResponse,
    ReportSnapshotCreate,
    ReportSnapshotRead,
    ReportSnapshotUpdate,
    ReportTemplateCreate,
    ReportTemplateRead,
    ReportTemplateUpdate,
    SchedulerRunResponse,
    ScanResultCreate,
    ScanResultFindingCreate,
    ScanResultFindingRead,
    ScanResultFindingUpdate,
    ScanResultRead,
    ScanResultUpdate,
    TargetAttributeDefinitionCreate,
    TargetAttributeDefinitionRead,
    TargetAttributeDefinitionUpdate,
    TargetAttributeAssignmentUpdateRequest,
    TargetAttributeValueCreate,
    TargetAttributeValueRead,
    TargetAttributeValueUpdate,
    TargetCreate,
    TargetDetailRead,
    TargetGroupCreate,
    TargetGroupAssignmentUpdateRequest,
    TargetGroupMemberUpdateRequest,
    TargetGroupMappingCreate,
    TargetGroupMappingRead,
    TargetGroupMappingUpdate,
    TargetGroupRead,
    TargetGroupUpdate,
    TargetImportResponse,
    TargetRead,
    TargetUpdate,
    TaskExecutionHeartbeatRequest,
    TaskExecutionHeartbeatResponse,
    TaskCreate,
    TaskExecutionCreate,
    TaskExecutionRead,
    TaskExecutionStatusRequest,
    TaskExecutionUpdate,
    TaskRead,
    TaskUpdate,
    LoginRequest,
    LoginResponse,
    UserAccountCreate,
    UserAccountRead,
    UserAccountUpdate,
    VulnerabilityCreate,
    VulnerabilityRead,
    VulnerabilityScriptCreate,
    VulnerabilityScriptRead,
    VulnerabilityScriptUpdate,
    VulnerabilityUpdate,
    WorkerRunResponse,
)
from app.services.auth import (
    authenticate_user,
    create_access_token,
    get_current_user_with_permissions,
    get_user_permissions,
    hash_password,
    require_permissions,
)
from app.services.agent_runtime import (
    get_execute_contract_document,
    update_agent_heartbeat,
    update_task_execution_heartbeat,
)
from app.services.execution import get_runtime_overview, launch_operation, update_task_execution_status
from app.services.result_exchange import export_operation_results, import_operation_results
from app.services.scan_results import normalize_and_store_scan_result
from app.services.scheduler import run_scheduler_cycle
from app.services.targets import (
    create_target,
    delete_target,
    delete_target_attribute_definition,
    delete_target_group,
    import_targets_from_file,
    list_targets_enriched,
    update_target,
    update_target_attribute_assignments,
    update_target_group_assignments,
)
from app.services.worker import run_worker_cycle

router = APIRouter()


def _payload_dict(payload: BaseModel) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True)


def register_crud_routes(
    api: APIRouter,
    *,
    path: str,
    model: type[Base],
    read_schema: type[BaseModel],
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    list_permission: str | None = None,
    write_permission: str | None = None,
) -> None:
    @api.get(path, response_model=list[read_schema])
    def list_items(
        db: Session = Depends(get_db),
        _current_user=Depends(require_permissions(*( [list_permission] if list_permission else [] ))),
    ):
        return db.scalars(select(model).order_by(model.id.desc())).all()

    @api.get(f"{path}/{{item_id}}", response_model=read_schema)
    def get_item(
        item_id: int,
        db: Session = Depends(get_db),
        _current_user=Depends(require_permissions(*( [list_permission] if list_permission else [] ))),
    ):
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return item

    @api.post(path, response_model=read_schema, status_code=status.HTTP_201_CREATED)
    def create_item(
        payload: create_schema,
        db: Session = Depends(get_db),
        _current_user=Depends(require_permissions(*( [write_permission] if write_permission else [] ))),
    ):
        item = model(**_payload_dict(payload))
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @api.put(f"{path}/{{item_id}}", response_model=read_schema)
    def update_item(
        item_id: int,
        payload: update_schema,
        db: Session = Depends(get_db),
        _current_user=Depends(require_permissions(*( [write_permission] if write_permission else [] ))),
    ):
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        for field, value in _payload_dict(payload).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item

    @api.delete(f"{path}/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(
        item_id: int,
        db: Session = Depends(get_db),
        _current_user=Depends(require_permissions(*( [write_permission] if write_permission else [] ))),
    ):
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        db.delete(item)
        db.commit()


register_crud_routes(
    router,
    path="/agents",
    model=Agent,
    read_schema=AgentRead,
    create_schema=AgentCreate,
    update_schema=AgentUpdate,
    list_permission="agents.manage",
    write_permission="agents.manage",
)
register_crud_routes(
    router,
    path="/account-groups",
    model=AccountGroup,
    read_schema=AccountGroupRead,
    create_schema=AccountGroupCreate,
    update_schema=AccountGroupUpdate,
    list_permission="auth.manage",
    write_permission="auth.manage",
)
register_crud_routes(
    router,
    path="/app-permissions",
    model=AppPermission,
    read_schema=AppPermissionRead,
    create_schema=AppPermissionCreate,
    update_schema=AppPermissionUpdate,
    list_permission="auth.manage",
    write_permission="auth.manage",
)
register_crud_routes(
    router,
    path="/tasks",
    model=Task,
    read_schema=TaskRead,
    create_schema=TaskCreate,
    update_schema=TaskUpdate,
    list_permission="tasks.manage",
    write_permission="tasks.manage",
)
register_crud_routes(
    router,
    path="/operations",
    model=Operation,
    read_schema=OperationRead,
    create_schema=OperationCreate,
    update_schema=OperationUpdate,
    list_permission="operations.manage",
    write_permission="operations.manage",
)
register_crud_routes(
    router,
    path="/operation-tasks",
    model=OperationTask,
    read_schema=OperationTaskRead,
    create_schema=OperationTaskCreate,
    update_schema=OperationTaskUpdate,
    list_permission="operations.manage",
    write_permission="operations.manage",
)
register_crud_routes(
    router,
    path="/operation-result-history",
    model=OperationResultImportExport,
    read_schema=OperationResultExchangeRead,
    create_schema=OperationResultExchangeCreate,
    update_schema=OperationResultExchangeUpdate,
    list_permission="reports.manage",
    write_permission="reports.manage",
)
register_crud_routes(
    router,
    path="/operation-executions",
    model=OperationExecution,
    read_schema=OperationExecutionRead,
    create_schema=OperationExecutionCreate,
    update_schema=OperationExecutionUpdate,
    list_permission="runtime.control",
    write_permission="runtime.control",
)
register_crud_routes(
    router,
    path="/task-executions",
    model=TaskExecution,
    read_schema=TaskExecutionRead,
    create_schema=TaskExecutionCreate,
    update_schema=TaskExecutionUpdate,
    list_permission="runtime.control",
    write_permission="runtime.control",
)
register_crud_routes(
    router,
    path="/targets",
    model=Target,
    read_schema=TargetRead,
    create_schema=TargetCreate,
    update_schema=TargetUpdate,
    list_permission="targets.manage",
    write_permission="targets.manage",
)
register_crud_routes(
    router,
    path="/target-attribute-definitions",
    model=TargetAttributeDefinition,
    read_schema=TargetAttributeDefinitionRead,
    create_schema=TargetAttributeDefinitionCreate,
    update_schema=TargetAttributeDefinitionUpdate,
    list_permission="targets.manage",
    write_permission="targets.manage",
)
register_crud_routes(
    router,
    path="/target-attribute-values",
    model=TargetAttributeValue,
    read_schema=TargetAttributeValueRead,
    create_schema=TargetAttributeValueCreate,
    update_schema=TargetAttributeValueUpdate,
    list_permission="targets.manage",
    write_permission="targets.manage",
)
register_crud_routes(
    router,
    path="/target-groups",
    model=TargetGroup,
    read_schema=TargetGroupRead,
    create_schema=TargetGroupCreate,
    update_schema=TargetGroupUpdate,
    list_permission="targets.manage",
    write_permission="targets.manage",
)
register_crud_routes(
    router,
    path="/target-group-mappings",
    model=TargetGroupMapping,
    read_schema=TargetGroupMappingRead,
    create_schema=TargetGroupMappingCreate,
    update_schema=TargetGroupMappingUpdate,
    list_permission="targets.manage",
    write_permission="targets.manage",
)
register_crud_routes(
    router,
    path="/vulnerabilities",
    model=Vulnerability,
    read_schema=VulnerabilityRead,
    create_schema=VulnerabilityCreate,
    update_schema=VulnerabilityUpdate,
    list_permission="vulnerabilities.manage",
    write_permission="vulnerabilities.manage",
)
register_crud_routes(
    router,
    path="/vulnerability-scripts",
    model=VulnerabilityScript,
    read_schema=VulnerabilityScriptRead,
    create_schema=VulnerabilityScriptCreate,
    update_schema=VulnerabilityScriptUpdate,
    list_permission="vulnerabilities.manage",
    write_permission="vulnerabilities.manage",
)
register_crud_routes(
    router,
    path="/scan-results",
    model=ScanResult,
    read_schema=ScanResultRead,
    create_schema=ScanResultCreate,
    update_schema=ScanResultUpdate,
    list_permission="scan_results.view",
    write_permission="runtime.control",
)
register_crud_routes(
    router,
    path="/scan-findings",
    model=ScanResultFinding,
    read_schema=ScanResultFindingRead,
    create_schema=ScanResultFindingCreate,
    update_schema=ScanResultFindingUpdate,
    list_permission="scan_results.view",
    write_permission="scan_results.view",
)
register_crud_routes(
    router,
    path="/generated-reports",
    model=GeneratedReport,
    read_schema=GeneratedReportRead,
    create_schema=GeneratedReportCreate,
    update_schema=GeneratedReportUpdate,
    list_permission="reports.manage",
    write_permission="reports.manage",
)
register_crud_routes(
    router,
    path="/report-snapshots",
    model=ReportSnapshot,
    read_schema=ReportSnapshotRead,
    create_schema=ReportSnapshotCreate,
    update_schema=ReportSnapshotUpdate,
    list_permission="reports.manage",
    write_permission="reports.manage",
)
register_crud_routes(
    router,
    path="/report-templates",
    model=ReportTemplate,
    read_schema=ReportTemplateRead,
    create_schema=ReportTemplateCreate,
    update_schema=ReportTemplateUpdate,
    list_permission="reports.manage",
    write_permission="reports.manage",
)


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user, permissions, expires_at = authenticate_user(db, payload.username, payload.password)
    access_token = create_access_token(user, permissions, expires_at)
    return LoginResponse(access_token=access_token, expires_at=expires_at, user=user, permissions=permissions)


@router.get("/auth/me", response_model=CurrentUserResponse)
def auth_me(current=Depends(get_current_user_with_permissions)):
    user, permissions = current
    return CurrentUserResponse(user=user, permissions=permissions)


@router.get("/account-groups/{group_id}/permissions", response_model=list[GroupPermissionItem])
def list_group_permissions(
    group_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("auth.manage")),
):
    group = db.get(AccountGroup, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    enabled_rows = db.scalars(
        select(AccountGroupPermission).where(AccountGroupPermission.group_id == group_id)
    ).all()
    enabled_map = {row.permission_id: row.is_enabled for row in enabled_rows}
    permissions = db.scalars(select(AppPermission).order_by(AppPermission.module_name.asc(), AppPermission.code.asc())).all()
    return [
        GroupPermissionItem(
            permission_id=permission.id,
            permission_code=permission.code,
            permission_name=permission.name,
            module_name=permission.module_name,
            is_enabled=enabled_map.get(permission.id, False),
        )
        for permission in permissions
    ]


@router.put("/account-groups/{group_id}/permissions", response_model=list[GroupPermissionItem])
def update_group_permissions(
    group_id: int,
    payload: GroupPermissionUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("auth.manage")),
):
    group = db.get(AccountGroup, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    existing = db.scalars(select(AccountGroupPermission).where(AccountGroupPermission.group_id == group_id)).all()
    existing_map = {item.permission_id: item for item in existing}
    for item in payload.items:
        row = existing_map.get(item.permission_id)
        if row:
            row.is_enabled = item.is_enabled
        else:
            db.add(
                AccountGroupPermission(group_id=group_id, permission_id=item.permission_id, is_enabled=item.is_enabled)
            )
    db.commit()
    return list_group_permissions(group_id, db)


@router.get("/user-accounts", response_model=list[UserAccountRead])
def list_user_accounts(
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("auth.manage")),
):
    return db.scalars(select(UserAccount).order_by(UserAccount.id.desc())).all()


@router.get("/user-accounts/{item_id}", response_model=UserAccountRead)
def get_user_account(
    item_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("auth.manage")),
):
    item = db.get(UserAccount, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post("/user-accounts", response_model=UserAccountRead, status_code=status.HTTP_201_CREATED)
def create_user_account(
    payload: UserAccountCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("auth.manage")),
):
    item = UserAccount(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        group_id=payload.group_id,
        is_active=payload.is_active,
        password_hash=hash_password(payload.password),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/user-accounts/{item_id}", response_model=UserAccountRead)
def update_user_account(
    item_id: int,
    payload: UserAccountUpdate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("auth.manage")),
):
    item = db.get(UserAccount, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    for field, value in _payload_dict(payload).items():
        if field == "password":
            item.password_hash = hash_password(value)
            continue
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/user-accounts/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(
    item_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("auth.manage")),
):
    item = db.get(UserAccount, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    db.delete(item)
    db.commit()


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("dashboard.view")),
):
    def count_rows(model: type[Base]) -> int:
        return db.scalar(select(func.count()).select_from(model)) or 0

    return DashboardSummary(
        agents=count_rows(Agent),
        tasks=count_rows(Task),
        operations=count_rows(Operation),
        operation_executions=count_rows(OperationExecution),
        task_executions=count_rows(TaskExecution),
        targets=count_rows(Target),
        vulnerabilities=count_rows(Vulnerability),
        scan_results=count_rows(ScanResult),
        open_findings=db.scalar(
            select(func.count()).select_from(ScanResultFinding).where(ScanResultFinding.status == "open")
        )
        or 0,
        report_templates=count_rows(ReportTemplate),
        generated_reports=count_rows(GeneratedReport),
    )


@router.get("/operations/{operation_id}/tasks", response_model=list[OperationTaskRead])
def list_operation_tasks(
    operation_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("operations.manage")),
):
    return db.scalars(
        select(OperationTask).where(OperationTask.operation_id == operation_id).order_by(OperationTask.order_index.asc())
    ).all()


@router.get("/targets-enriched", response_model=list[TargetDetailRead])
def list_targets_with_details(
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    return list_targets_enriched(db)


@router.post("/targets/manage", response_model=TargetRead, status_code=status.HTTP_201_CREATED)
def create_target_item(
    payload: TargetCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    return create_target(db, payload.model_dump(exclude_unset=True))


@router.put("/targets/manage/{target_id}", response_model=TargetRead)
def update_target_item(
    target_id: int,
    payload: TargetUpdate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    item = db.get(Target, target_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return update_target(db, item, payload.model_dump(exclude_unset=True))


@router.delete("/targets/manage/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target_item(
    target_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    item = db.get(Target, target_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    delete_target(db, item)


@router.put("/targets/{target_id}/attribute-values", response_model=list[TargetAttributeValueRead])
def set_target_attribute_values(
    target_id: int,
    payload: TargetAttributeAssignmentUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    if not db.get(Target, target_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return update_target_attribute_assignments(db, target_id, payload)


@router.put("/targets/{target_id}/groups", response_model=list[TargetGroupMappingRead])
def set_target_groups(
    target_id: int,
    payload: TargetGroupAssignmentUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    if not db.get(Target, target_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return update_target_group_assignments(db, target_id, payload)


@router.put("/target-groups/{group_id}/targets", response_model=list[TargetGroupMappingRead])
def set_group_targets(
    group_id: int,
    payload: TargetGroupMemberUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    group = db.get(TargetGroup, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target group not found")

    existing = db.scalars(select(TargetGroupMapping).where(TargetGroupMapping.target_group_id == group_id)).all()
    existing_ids = {item.target_id for item in existing}
    desired_ids = set(payload.target_ids)

    for item in existing:
        if item.target_id not in desired_ids:
            db.delete(item)

    for target_id in desired_ids - existing_ids:
        if db.get(Target, target_id):
            db.add(TargetGroupMapping(target_id=target_id, target_group_id=group_id))

    db.commit()
    return db.scalars(select(TargetGroupMapping).where(TargetGroupMapping.target_group_id == group_id)).all()


@router.post("/targets/import", response_model=TargetImportResponse, status_code=status.HTTP_201_CREATED)
async def import_targets(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Thiếu tên file import.")
    content = await file.read()
    try:
        return import_targets_from_file(db, file.filename, content)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.post("/target-attribute-definitions/manage", response_model=TargetAttributeDefinitionRead, status_code=status.HTTP_201_CREATED)
def create_target_attribute_definition_item(
    payload: TargetAttributeDefinitionCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    item = TargetAttributeDefinition(
        attribute_code=payload.attribute_code or "",
        attribute_name=payload.attribute_name,
        data_type=payload.data_type,
        is_required=payload.is_required,
        default_value=payload.default_value,
        description=payload.description,
    )
    if not item.attribute_code:
        item.attribute_code = item.attribute_name.lower().strip().replace(" ", "_")[:50]
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/target-attribute-definitions/manage/{definition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target_attribute_definition_item(
    definition_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    item = db.get(TargetAttributeDefinition, definition_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target attribute definition not found")
    delete_target_attribute_definition(db, item)


@router.post("/target-groups/manage", response_model=TargetGroupRead, status_code=status.HTTP_201_CREATED)
def create_target_group_item(
    payload: TargetGroupCreate,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    item = TargetGroup(
        code=payload.code or payload.name.lower().strip().replace(" ", "_")[:50],
        name=payload.name,
        description=payload.description,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/target-groups/manage/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target_group_item(
    group_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("targets.manage")),
):
    item = db.get(TargetGroup, group_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target group not found")
    delete_target_group(db, item)


@router.post("/operations/{operation_id}/launch", response_model=OperationLaunchResponse)
def execute_operation(
    operation_id: int,
    payload: OperationLaunchRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("runtime.control")),
):
    execution, task_executions = launch_operation(db, operation_id, payload)
    return OperationLaunchResponse(execution=execution, task_executions=task_executions)


@router.get("/agents/runtime/execute-contract", response_model=AgentExecuteContractDocument)
def get_agent_execute_contract():
    return get_execute_contract_document()


@router.post("/agents/heartbeat", response_model=AgentHeartbeatResponse)
def record_agent_heartbeat(payload: AgentHeartbeatRequest, db: Session = Depends(get_db)):
    agent, acknowledged_at = update_agent_heartbeat(db, payload)
    return AgentHeartbeatResponse(
        acknowledged_at=acknowledged_at,
        agent=agent,
        metadata_json=payload.metadata_json,
    )


@router.get("/operations/runtime/overview", response_model=list[OperationRuntimeOverviewItem])
def operations_runtime_overview(
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("runtime.control")),
):
    return get_runtime_overview(db)


@router.post("/scheduler/run", response_model=SchedulerRunResponse)
def run_scheduler_now(
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("runtime.control")),
):
    return run_scheduler_cycle(db)


@router.post("/worker/run", response_model=WorkerRunResponse)
def run_worker_now(
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("runtime.control")),
):
    return run_worker_cycle(db)


@router.post("/demo/mock-flow", response_model=DemoMockFlowResponse)
def run_mock_demo_flow(
    payload: DemoMockFlowRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("runtime.control")),
):
    operation = db.get(Operation, payload.operation_id) if payload.operation_id else db.scalar(select(Operation).limit(1))
    if not operation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No operation found")
    target = db.get(Target, payload.target_id) if payload.target_id else db.scalar(select(Target).limit(1))
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No target found")

    execution, task_executions = launch_operation(
        db,
        operation.id,
        OperationLaunchRequest(trigger_type="manual", shared_input={"target_id": target.id}),
    )
    worker_summary = run_worker_cycle(db)
    findings_created = db.scalar(
        select(func.count())
        .select_from(ScanResultFinding)
        .join(ScanResult, ScanResultFinding.scan_result_id == ScanResult.id)
        .where(ScanResult.operation_execution_id == execution.id)
    ) or 0
    db.refresh(execution)
    return DemoMockFlowResponse(
        operation_id=operation.id,
        operation_execution_id=execution.id,
        task_execution_ids=[item.id for item in task_executions],
        findings_created=findings_created,
        execution_status=execution.status,
        worker_summary=worker_summary,
    )


@router.post("/operations/{operation_id}/results/export", response_model=OperationResultExportResponse)
def export_results(
    operation_id: int,
    payload: OperationResultExportRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("reports.manage")),
):
    history, exported_records = export_operation_results(db, operation_id, payload.file_format)
    return OperationResultExportResponse(history=history, exported_records=exported_records)


@router.post("/operations/{operation_id}/results/import", response_model=OperationResultImportResponse)
def import_results(
    operation_id: int,
    payload: OperationResultImportRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("reports.manage")),
):
    history, imported_scan_results, imported_findings = import_operation_results(db, operation_id, payload.payload_json)
    return OperationResultImportResponse(
        history=history,
        imported_scan_results=imported_scan_results,
        imported_findings=imported_findings,
    )


@router.get("/operation-executions/{execution_id}/tasks", response_model=list[TaskExecutionRead])
def list_execution_tasks(
    execution_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("runtime.control")),
):
    return db.scalars(
        select(TaskExecution)
        .where(TaskExecution.operation_execution_id == execution_id)
        .order_by(TaskExecution.id.asc())
    ).all()


@router.post("/task-executions/{task_execution_id}/status", response_model=TaskExecutionRead)
def set_task_execution_status(
    task_execution_id: int,
    payload: TaskExecutionStatusRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(require_permissions("runtime.control")),
):
    task_execution, _operation_execution = update_task_execution_status(db, task_execution_id, payload)
    return task_execution


@router.post("/task-executions/{task_execution_id}/heartbeat", response_model=TaskExecutionHeartbeatResponse)
def heartbeat_task_execution(
    task_execution_id: int, payload: TaskExecutionHeartbeatRequest, db: Session = Depends(get_db)
):
    task_execution, operation_execution, acknowledged_at = update_task_execution_heartbeat(db, task_execution_id, payload)
    return TaskExecutionHeartbeatResponse(
        acknowledged_at=acknowledged_at,
        operation_execution=operation_execution,
        task_execution=task_execution,
    )


@router.post("/scan-results/normalize", response_model=ParserNormalizeResponse, status_code=status.HTTP_201_CREATED)
def normalize_scan_result(payload: ParserNormalizeRequest, db: Session = Depends(get_db)):
    scan_result, findings = normalize_and_store_scan_result(
        db,
        agent_type=payload.agent_type,
        source_tool=payload.source_tool,
        raw_output=payload.raw_output,
        operation_execution_id=payload.operation_execution_id,
        task_execution_id=payload.task_execution_id,
        target_id=payload.target_id,
        detected_at=payload.detected_at,
    )
    db.commit()
    db.refresh(scan_result)
    for finding in findings:
        db.refresh(finding)

    return ParserNormalizeResponse(scan_result=scan_result, findings=findings)
