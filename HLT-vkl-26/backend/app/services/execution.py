from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Agent, Operation, OperationExecution, OperationTask, TaskExecution
from app.schemas.resources import OperationLaunchRequest, OperationRuntimeOverviewItem, TaskExecutionStatusRequest
from app.services.pkt_scanner_results import build_pkt_scan_entries, build_pkt_scan_folder_name, ingest_pkt_scan_output


def _build_execution_code(operation_code: str) -> str:
    return f"{operation_code}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


def launch_operation(db: Session, operation_id: int, payload: OperationLaunchRequest) -> tuple[OperationExecution, list[TaskExecution]]:
    operation = db.get(Operation, operation_id)
    if not operation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")

    operation_tasks = db.scalars(
        select(OperationTask).where(OperationTask.operation_id == operation_id).order_by(OperationTask.order_index.asc())
    ).all()
    if not operation_tasks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Operation has no tasks to execute")

    execution = OperationExecution(
        operation_id=operation.id,
        execution_code=_build_execution_code(operation.code),
        trigger_type=payload.trigger_type,
        status="queued",
        started_at=datetime.utcnow(),
        year=payload.year,
        quarter=payload.quarter,
        week=payload.week,
        note=payload.note,
        source_root_path=payload.source_root_path,
        selected_target_ids_json=payload.target_ids or None,
        summary_json={
            "task_count": len(operation_tasks),
            "shared_input": payload.shared_input or {},
            "selected_target_count": len(payload.target_ids or []),
        },
    )
    db.add(execution)
    db.flush()

    task_executions: list[TaskExecution] = []
    shared_input = payload.shared_input or {}
    scan_entries, selected_targets = build_pkt_scan_entries(db, payload.target_ids or [])
    folder_name = build_pkt_scan_folder_name(operation, execution)

    for operation_task in operation_tasks:
        assigned_agent = db.scalar(
            select(Agent)
            .where(Agent.agent_type == operation_task.task.agent_type)
            .where(Agent.status == "online")
            .order_by(Agent.last_seen_at.desc(), Agent.id.asc())
            .limit(1)
        )
        if not assigned_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No online agent available for task type '{operation_task.task.agent_type}'",
            )

        input_payload = dict(shared_input)
        if payload.target_ids:
            input_payload["target_ids"] = payload.target_ids
            input_payload.setdefault("target_id", payload.target_ids[0])
            input_payload["selected_target_ids"] = payload.target_ids
            input_payload["selected_targets"] = [
                {
                    "id": target.id,
                    "code": target.code,
                    "name": target.name,
                    "ip_range": target.ip_range,
                }
                for target in selected_targets
            ]
            input_payload["scan_entries"] = scan_entries
            input_payload["folder_name"] = folder_name
        if operation_task.input_override_json:
            input_payload.update(operation_task.input_override_json)

        task_execution = TaskExecution(
            operation_execution_id=execution.id,
            operation_task_id=operation_task.id,
            task_id=operation_task.task_id,
            agent_id=assigned_agent.id,
            status="queued",
            input_data_json=input_payload or None,
            started_at=None,
            finished_at=None,
        )
        db.add(task_execution)
        task_executions.append(task_execution)

    db.commit()
    db.refresh(execution)
    for task_execution in task_executions:
        db.refresh(task_execution)

    return execution, task_executions


def update_task_execution_status(
    db: Session, task_execution_id: int, payload: TaskExecutionStatusRequest
) -> tuple[TaskExecution, OperationExecution]:
    task_execution = db.get(TaskExecution, task_execution_id)
    if not task_execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task execution not found")

    task_execution.status = payload.status
    output_payload = dict(payload.output_data_json or {})
    raw_log = payload.raw_log
    if payload.status == "completed" and payload.raw_output and task_execution.task.code == "TASK-PKT-SCANNING":
        try:
            pkt_payload = ingest_pkt_scan_output(db, task_execution, payload.raw_output)
            output_payload.update(pkt_payload)
            if pkt_payload.get("warnings"):
                raw_log = "\n".join(pkt_payload["warnings"])
        except Exception as exc:  # noqa: BLE001
            task_execution.status = "failed"
            raw_log = f"PKT scanner result ingest failed: {exc}"

    if payload.output_data_json is not None:
        task_execution.output_data_json = output_payload
    if raw_log is not None:
        task_execution.raw_log = raw_log

    now = datetime.utcnow()
    if payload.status == "running" and task_execution.started_at is None:
        task_execution.started_at = now
    if payload.status in {"completed", "failed", "canceled"} and task_execution.finished_at is None:
        if task_execution.started_at is None:
            task_execution.started_at = now
        task_execution.finished_at = now

    operation_execution = db.get(OperationExecution, task_execution.operation_execution_id)
    if not operation_execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent operation execution not found")

    refresh_operation_execution_summary(db, operation_execution.id, now)

    db.commit()
    db.refresh(task_execution)
    db.refresh(operation_execution)
    return task_execution, operation_execution


def refresh_operation_execution_summary(
    db: Session, operation_execution_id: int, now: datetime | None = None
) -> OperationExecution:
    current_time = now or datetime.utcnow()
    operation_execution = db.get(OperationExecution, operation_execution_id)
    if not operation_execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent operation execution not found")

    sibling_tasks = db.scalars(
        select(TaskExecution).where(TaskExecution.operation_execution_id == operation_execution.id).order_by(TaskExecution.id.asc())
    ).all()

    queued_count = sum(1 for item in sibling_tasks if item.status == "queued")
    running_count = sum(1 for item in sibling_tasks if item.status == "running")
    failed_count = sum(1 for item in sibling_tasks if item.status == "failed")
    completed_count = sum(1 for item in sibling_tasks if item.status == "completed")
    canceled_count = sum(1 for item in sibling_tasks if item.status == "canceled")
    total_count = len(sibling_tasks)

    if running_count > 0:
        operation_execution.status = "running"
        if operation_execution.started_at is None:
            operation_execution.started_at = current_time
    elif failed_count > 0:
        operation_execution.status = "failed"
        operation_execution.finished_at = current_time
    elif completed_count + canceled_count == total_count and total_count > 0:
        operation_execution.status = "completed"
        operation_execution.finished_at = current_time
    else:
        operation_execution.status = "queued"

    summary_payload = dict(operation_execution.summary_json or {})
    summary_payload.update(
        {
            "task_count": total_count,
            "queued_count": queued_count,
            "running_count": running_count,
            "failed_count": failed_count,
            "completed_count": completed_count,
            "canceled_count": canceled_count,
        }
    )
    operation_execution.summary_json = summary_payload
    return operation_execution


def get_runtime_overview(db: Session) -> list[OperationRuntimeOverviewItem]:
    operations = db.scalars(select(Operation).order_by(Operation.id.asc())).all()
    overview: list[OperationRuntimeOverviewItem] = []

    for operation in operations:
        executions = db.scalars(
            select(OperationExecution)
            .where(OperationExecution.operation_id == operation.id)
            .order_by(OperationExecution.created_at.desc(), OperationExecution.id.desc())
        ).all()
        latest_execution = executions[0] if executions else None

        queued_tasks = running_tasks = failed_tasks = completed_tasks = 0
        if latest_execution:
            status_rows = db.execute(
                select(TaskExecution.status, func.count(TaskExecution.id))
                .where(TaskExecution.operation_execution_id == latest_execution.id)
                .group_by(TaskExecution.status)
            ).all()
            counts = {status_name: count for status_name, count in status_rows}
            queued_tasks = counts.get("queued", 0)
            running_tasks = counts.get("running", 0)
            failed_tasks = counts.get("failed", 0)
            completed_tasks = counts.get("completed", 0)

        overview.append(
            OperationRuntimeOverviewItem(
                operation_id=operation.id,
                operation_code=operation.code,
                operation_name=operation.name,
                total_executions=len(executions),
                latest_execution_id=latest_execution.id if latest_execution else None,
                latest_execution_status=latest_execution.status if latest_execution else None,
                queued_tasks=queued_tasks,
                running_tasks=running_tasks,
                failed_tasks=failed_tasks,
                completed_tasks=completed_tasks,
            )
        )

    return overview
