from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agent, Operation, OperationExecution, OperationTask, TaskExecution
from app.schemas.resources import OperationLaunchRequest


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
        summary_json={"task_count": len(operation_tasks), "shared_input": payload.shared_input or {}},
    )
    db.add(execution)
    db.flush()

    task_executions: list[TaskExecution] = []
    shared_input = payload.shared_input or {}

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
