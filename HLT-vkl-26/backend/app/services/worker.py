import json
import threading
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Operation, OperationExecution, OperationTask, Target, TaskExecution
from app.schemas.resources import WorkerRunResponse
from app.services.agents.dispatch import dispatch_task_to_agent
from app.services.agents.registry import has_parser
from app.services.agent_monitoring import DEFAULT_READY_NOTE, ERROR_STATUS, READY_STATUS, WORKING_STATUS, mark_agent_status
from app.services.execution import refresh_operation_execution_summary
from app.services.pkt_scanner_results import ingest_pkt_scan_output
from app.services.scan_results import normalize_and_store_scan_result


def _resolve_target(db: Session, task_execution: TaskExecution) -> tuple[Target | None, str]:
    input_data = task_execution.input_data_json or {}
    target_id = input_data.get("target_id")
    if target_id:
        target = db.get(Target, int(target_id))
        if target:
            return target, target.ip_range or target.domain or target.name

    target_ids = input_data.get("target_ids") or []
    if isinstance(target_ids, list):
        for selected_target_id in target_ids:
            try:
                target = db.get(Target, int(selected_target_id))
            except (TypeError, ValueError):
                target = None
            if target:
                return target, target.ip_range or target.domain or target.name

    target = db.scalar(select(Target).order_by(Target.id.asc()).limit(1))
    if target:
        return target, target.ip_range or target.domain or target.name
    return None, "127.0.0.1"


def _previous_gate_allows_run(db: Session, task_execution: TaskExecution) -> bool:
    current_operation_task = db.get(OperationTask, task_execution.operation_task_id)
    if not current_operation_task:
        return False

    previous_tasks = db.scalars(
        select(TaskExecution)
        .join(OperationTask, TaskExecution.operation_task_id == OperationTask.id)
        .where(TaskExecution.operation_execution_id == task_execution.operation_execution_id)
        .where(OperationTask.order_index < current_operation_task.order_index)
        .order_by(OperationTask.order_index.asc(), TaskExecution.id.asc())
    ).all()

    for previous in previous_tasks:
        previous_operation_task = db.get(OperationTask, previous.operation_task_id)
        if previous.status == "completed":
            continue
        if previous.status == "failed" and previous_operation_task and previous_operation_task.continue_on_error:
            continue
        return False

    return True


def _task_concurrency_allows_run(db: Session, task_execution: TaskExecution) -> bool:
    max_concurrency = getattr(task_execution.task, "max_concurrency_per_agent", 0) or 0
    if max_concurrency <= 0:
        return True

    running_count = db.scalar(
        select(func.count(TaskExecution.id))
        .where(TaskExecution.agent_id == task_execution.agent_id)
        .where(TaskExecution.task_id == task_execution.task_id)
        .where(TaskExecution.status == "running")
        .where(TaskExecution.id != task_execution.id)
    )
    return (running_count or 0) < max_concurrency


def _cancel_blocked_followups(db: Session, failed_task_execution: TaskExecution) -> int:
    failed_operation_task = db.get(OperationTask, failed_task_execution.operation_task_id)
    if not failed_operation_task or failed_operation_task.continue_on_error:
        return 0

    queued_followups = db.scalars(
        select(TaskExecution)
        .join(OperationTask, TaskExecution.operation_task_id == OperationTask.id)
        .where(TaskExecution.operation_execution_id == failed_task_execution.operation_execution_id)
        .where(TaskExecution.status == "queued")
        .where(OperationTask.order_index > failed_operation_task.order_index)
    ).all()

    for task_execution in queued_followups:
        task_execution.status = "canceled"
        task_execution.started_at = datetime.utcnow()
        task_execution.finished_at = datetime.utcnow()
        task_execution.raw_log = "Canceled because previous task failed and continue_on_error is false."

    return len(queued_followups)


def _operation_task_note(db: Session, task_execution: TaskExecution) -> str:
    operation_name = db.scalar(
        select(Operation.name)
        .join(OperationExecution, Operation.id == OperationExecution.operation_id)
        .where(OperationExecution.id == task_execution.operation_execution_id)
    )
    return f"{operation_name or 'Operation'} / {task_execution.task.name}"


def process_task_execution(db: Session, task_execution: TaskExecution) -> str:
    task_execution.status = "running"
    task_execution.started_at = datetime.utcnow()
    if task_execution.agent:
        mark_agent_status(task_execution.agent, WORKING_STATUS, _operation_task_note(db, task_execution), task_execution.started_at)

    target, target_value = _resolve_target(db, task_execution)

    try:
        raw_output, execution_meta = dispatch_task_to_agent(task_execution.agent, task_execution, target_value, target)
        task_execution.output_data_json = {"target": target_value, **execution_meta}
        dispatch_status = execution_meta.get("dispatch_status")
        if dispatch_status in {"accepted", "running", "queued"}:
            task_execution.raw_log = execution_meta.get("response_meta", {}).get(
                "message", f"Agent accepted task via {execution_meta.get('mode')}."
            )
            task_execution.status = "running"
            task_execution.finished_at = None
            if task_execution.agent:
                mark_agent_status(
                    task_execution.agent,
                    WORKING_STATUS,
                    _operation_task_note(db, task_execution),
                    datetime.utcnow(),
                )
            return "running"

        task_execution.raw_log = f"Executed task via {execution_meta.get('mode')} for {task_execution.task.agent_type}."
        if task_execution.task.code == "TASK-PKT-SCANNING" and raw_output is not None:
            parsed_output = json.loads(raw_output)
            result_code = int(parsed_output.get("result_code") or 500)
            if result_code != 200:
                message = parsed_output.get("message") or f"PKT Scanning failed with code {result_code}"
                raise RuntimeError(message)

            pkt_payload = ingest_pkt_scan_output(db, task_execution, raw_output)
            task_execution.output_data_json = {"target": target_value, **execution_meta, **pkt_payload}
            task_execution.raw_log = pkt_payload.get("warnings") and "\n".join(pkt_payload["warnings"]) or task_execution.raw_log

        task_execution.status = "completed"
        task_execution.finished_at = datetime.utcnow()
        if task_execution.agent:
            mark_agent_status(task_execution.agent, READY_STATUS, DEFAULT_READY_NOTE, task_execution.finished_at)

        if target is not None and raw_output is not None and has_parser(task_execution.task.agent_type):
            normalize_and_store_scan_result(
                db,
                agent_type=task_execution.task.agent_type,
                source_tool=task_execution.task.agent_type,
                raw_output=raw_output,
                operation_execution_id=task_execution.operation_execution_id,
                task_execution_id=task_execution.id,
                target_id=target.id,
                detected_at=datetime.utcnow(),
            )
        return "completed"
    except Exception as exc:  # noqa: BLE001
        task_execution.status = "failed"
        task_execution.raw_log = f"Worker failed: {exc}"
        task_execution.finished_at = datetime.utcnow()
        if task_execution.agent:
            mark_agent_status(task_execution.agent, ERROR_STATUS, str(exc), task_execution.finished_at)
        return "failed"


def run_worker_cycle(db: Session) -> WorkerRunResponse:
    started_at = datetime.utcnow()
    queued_tasks = db.scalars(
        select(TaskExecution)
        .where(TaskExecution.status == "queued")
        .order_by(TaskExecution.operation_execution_id.asc(), TaskExecution.id.asc())
    ).all()

    processed_execution_ids: list[int] = []
    processed_tasks = completed_tasks = failed_tasks = canceled_tasks = 0
    checked_execution_ids = {task.operation_execution_id for task in queued_tasks}

    for task_execution in queued_tasks:
        if not _previous_gate_allows_run(db, task_execution):
            continue
        if not _task_concurrency_allows_run(db, task_execution):
            continue
        result = process_task_execution(db, task_execution)
        processed_tasks += 1
        processed_execution_ids.append(task_execution.operation_execution_id)
        if result == "completed":
            completed_tasks += 1
        elif result == "failed":
            failed_tasks += 1
            canceled_tasks += _cancel_blocked_followups(db, task_execution)
        refresh_operation_execution_summary(db, task_execution.operation_execution_id)

    db.commit()
    return WorkerRunResponse(
        checked_executions=len(checked_execution_ids),
        processed_tasks=processed_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        canceled_tasks=canceled_tasks,
        processed_execution_ids=sorted(set(processed_execution_ids)),
        run_started_at=started_at,
    )


class WorkerLoop:
    def __init__(self, poll_seconds: int) -> None:
        self.poll_seconds = max(5, poll_seconds)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="hlt-worker-loop", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            db = SessionLocal()
            try:
                run_worker_cycle(db)
            finally:
                db.close()
            self._stop_event.wait(self.poll_seconds)
