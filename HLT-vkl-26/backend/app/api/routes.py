from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import get_db
from app.models import (
    Agent,
    GeneratedReport,
    Operation,
    OperationExecution,
    OperationTask,
    ReportTemplate,
    ReportSnapshot,
    ScanResult,
    ScanResultFinding,
    Target,
    TargetAttributeDefinition,
    TargetAttributeValue,
    TargetGroup,
    Task,
    TaskExecution,
    Vulnerability,
    VulnerabilityScript,
)
from app.schemas.resources import (
    AgentCreate,
    AgentRead,
    AgentUpdate,
    DashboardSummary,
    GeneratedReportCreate,
    GeneratedReportRead,
    GeneratedReportUpdate,
    OperationCreate,
    OperationExecutionCreate,
    OperationExecutionRead,
    OperationExecutionUpdate,
    OperationLaunchRequest,
    OperationLaunchResponse,
    OperationRead,
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
    TargetAttributeValueCreate,
    TargetAttributeValueRead,
    TargetAttributeValueUpdate,
    TargetCreate,
    TargetGroupCreate,
    TargetGroupRead,
    TargetGroupUpdate,
    TargetRead,
    TargetUpdate,
    TaskCreate,
    TaskExecutionCreate,
    TaskExecutionRead,
    TaskExecutionStatusRequest,
    TaskExecutionUpdate,
    TaskRead,
    TaskUpdate,
    VulnerabilityCreate,
    VulnerabilityRead,
    VulnerabilityScriptCreate,
    VulnerabilityScriptRead,
    VulnerabilityScriptUpdate,
    VulnerabilityUpdate,
    WorkerRunResponse,
)
from app.services.execution import get_runtime_overview, launch_operation, update_task_execution_status
from app.services.scan_results import normalize_and_store_scan_result
from app.services.scheduler import run_scheduler_cycle
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
) -> None:
    @api.get(path, response_model=list[read_schema])
    def list_items(db: Session = Depends(get_db)):
        return db.scalars(select(model).order_by(model.id.desc())).all()

    @api.get(f"{path}/{{item_id}}", response_model=read_schema)
    def get_item(item_id: int, db: Session = Depends(get_db)):
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        return item

    @api.post(path, response_model=read_schema, status_code=status.HTTP_201_CREATED)
    def create_item(payload: create_schema, db: Session = Depends(get_db)):
        item = model(**_payload_dict(payload))
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @api.put(f"{path}/{{item_id}}", response_model=read_schema)
    def update_item(item_id: int, payload: update_schema, db: Session = Depends(get_db)):
        item = db.get(model, item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        for field, value in _payload_dict(payload).items():
            setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item

    @api.delete(f"{path}/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(item_id: int, db: Session = Depends(get_db)):
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
)
register_crud_routes(
    router,
    path="/tasks",
    model=Task,
    read_schema=TaskRead,
    create_schema=TaskCreate,
    update_schema=TaskUpdate,
)
register_crud_routes(
    router,
    path="/operations",
    model=Operation,
    read_schema=OperationRead,
    create_schema=OperationCreate,
    update_schema=OperationUpdate,
)
register_crud_routes(
    router,
    path="/operation-tasks",
    model=OperationTask,
    read_schema=OperationTaskRead,
    create_schema=OperationTaskCreate,
    update_schema=OperationTaskUpdate,
)
register_crud_routes(
    router,
    path="/operation-executions",
    model=OperationExecution,
    read_schema=OperationExecutionRead,
    create_schema=OperationExecutionCreate,
    update_schema=OperationExecutionUpdate,
)
register_crud_routes(
    router,
    path="/task-executions",
    model=TaskExecution,
    read_schema=TaskExecutionRead,
    create_schema=TaskExecutionCreate,
    update_schema=TaskExecutionUpdate,
)
register_crud_routes(
    router,
    path="/targets",
    model=Target,
    read_schema=TargetRead,
    create_schema=TargetCreate,
    update_schema=TargetUpdate,
)
register_crud_routes(
    router,
    path="/target-attribute-definitions",
    model=TargetAttributeDefinition,
    read_schema=TargetAttributeDefinitionRead,
    create_schema=TargetAttributeDefinitionCreate,
    update_schema=TargetAttributeDefinitionUpdate,
)
register_crud_routes(
    router,
    path="/target-attribute-values",
    model=TargetAttributeValue,
    read_schema=TargetAttributeValueRead,
    create_schema=TargetAttributeValueCreate,
    update_schema=TargetAttributeValueUpdate,
)
register_crud_routes(
    router,
    path="/target-groups",
    model=TargetGroup,
    read_schema=TargetGroupRead,
    create_schema=TargetGroupCreate,
    update_schema=TargetGroupUpdate,
)
register_crud_routes(
    router,
    path="/vulnerabilities",
    model=Vulnerability,
    read_schema=VulnerabilityRead,
    create_schema=VulnerabilityCreate,
    update_schema=VulnerabilityUpdate,
)
register_crud_routes(
    router,
    path="/vulnerability-scripts",
    model=VulnerabilityScript,
    read_schema=VulnerabilityScriptRead,
    create_schema=VulnerabilityScriptCreate,
    update_schema=VulnerabilityScriptUpdate,
)
register_crud_routes(
    router,
    path="/scan-results",
    model=ScanResult,
    read_schema=ScanResultRead,
    create_schema=ScanResultCreate,
    update_schema=ScanResultUpdate,
)
register_crud_routes(
    router,
    path="/scan-findings",
    model=ScanResultFinding,
    read_schema=ScanResultFindingRead,
    create_schema=ScanResultFindingCreate,
    update_schema=ScanResultFindingUpdate,
)
register_crud_routes(
    router,
    path="/generated-reports",
    model=GeneratedReport,
    read_schema=GeneratedReportRead,
    create_schema=GeneratedReportCreate,
    update_schema=GeneratedReportUpdate,
)
register_crud_routes(
    router,
    path="/report-snapshots",
    model=ReportSnapshot,
    read_schema=ReportSnapshotRead,
    create_schema=ReportSnapshotCreate,
    update_schema=ReportSnapshotUpdate,
)
register_crud_routes(
    router,
    path="/report-templates",
    model=ReportTemplate,
    read_schema=ReportTemplateRead,
    create_schema=ReportTemplateCreate,
    update_schema=ReportTemplateUpdate,
)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
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
def list_operation_tasks(operation_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(OperationTask).where(OperationTask.operation_id == operation_id).order_by(OperationTask.order_index.asc())
    ).all()


@router.post("/operations/{operation_id}/launch", response_model=OperationLaunchResponse)
def execute_operation(operation_id: int, payload: OperationLaunchRequest, db: Session = Depends(get_db)):
    execution, task_executions = launch_operation(db, operation_id, payload)
    return OperationLaunchResponse(execution=execution, task_executions=task_executions)


@router.get("/operations/runtime/overview", response_model=list[OperationRuntimeOverviewItem])
def operations_runtime_overview(db: Session = Depends(get_db)):
    return get_runtime_overview(db)


@router.post("/scheduler/run", response_model=SchedulerRunResponse)
def run_scheduler_now(db: Session = Depends(get_db)):
    return run_scheduler_cycle(db)


@router.post("/worker/run", response_model=WorkerRunResponse)
def run_worker_now(db: Session = Depends(get_db)):
    return run_worker_cycle(db)


@router.get("/operation-executions/{execution_id}/tasks", response_model=list[TaskExecutionRead])
def list_execution_tasks(execution_id: int, db: Session = Depends(get_db)):
    return db.scalars(
        select(TaskExecution)
        .where(TaskExecution.operation_execution_id == execution_id)
        .order_by(TaskExecution.id.asc())
    ).all()


@router.post("/task-executions/{task_execution_id}/status", response_model=TaskExecutionRead)
def set_task_execution_status(
    task_execution_id: int, payload: TaskExecutionStatusRequest, db: Session = Depends(get_db)
):
    task_execution, _operation_execution = update_task_execution_status(db, task_execution_id, payload)
    return task_execution


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
