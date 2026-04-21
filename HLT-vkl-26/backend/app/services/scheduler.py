import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Operation, OperationExecution
from app.schemas.resources import OperationLaunchRequest, SchedulerRunResponse
from app.services.execution import launch_operation


@dataclass
class SchedulerDecision:
    should_run: bool
    reason: str


def _cron_weekday(now: datetime) -> int:
    return (now.weekday() + 1) % 7


def _match_cron_field(field: str, current: int) -> bool:
    if field == "*":
        return True

    for part in field.split(","):
        token = part.strip()
        if not token:
            continue
        if token == "*":
            return True
        if token.startswith("*/"):
            try:
                step = int(token[2:])
            except ValueError:
                continue
            if step > 0 and current % step == 0:
                return True
            continue
        if token.isdigit() and int(token) == current:
            return True
        if token == "7" and current == 0:
            return True
    return False


def _matches_cron(expression: str, now: datetime) -> bool:
    parts = expression.split()
    if len(parts) != 5:
        return False

    minute, hour, day, month, weekday = parts
    return all(
        [
            _match_cron_field(minute, now.minute),
            _match_cron_field(hour, now.hour),
            _match_cron_field(day, now.day),
            _match_cron_field(month, now.month),
            _match_cron_field(weekday, _cron_weekday(now)),
        ]
    )


def _interval_delta(config: dict | None) -> timedelta:
    schedule = config or {}
    interval_minutes = schedule.get("interval_minutes") or schedule.get("every_minutes")
    interval_hours = schedule.get("interval_hours") or schedule.get("hours")

    if interval_minutes:
        return timedelta(minutes=int(interval_minutes))
    if interval_hours:
        return timedelta(hours=int(interval_hours))
    return timedelta(hours=24)


def _latest_execution(db: Session, operation_id: int) -> OperationExecution | None:
    return db.scalar(
        select(OperationExecution)
        .where(OperationExecution.operation_id == operation_id)
        .order_by(OperationExecution.created_at.desc(), OperationExecution.id.desc())
        .limit(1)
    )


def _has_active_execution(db: Session, operation_id: int) -> bool:
    return db.scalar(
        select(OperationExecution)
        .where(OperationExecution.operation_id == operation_id)
        .where(OperationExecution.status.in_(["queued", "running"]))
        .limit(1)
    ) is not None


def should_run_operation(db: Session, operation: Operation, now: datetime | None = None) -> SchedulerDecision:
    current_time = now or datetime.utcnow()
    if not operation.is_active:
        return SchedulerDecision(False, "operation is inactive")
    if operation.schedule_type == "none":
        return SchedulerDecision(False, "operation has no schedule")
    if _has_active_execution(db, operation.id):
        return SchedulerDecision(False, "operation already has queued/running execution")

    latest_execution = _latest_execution(db, operation.id)

    if operation.schedule_type == "interval":
        delta = _interval_delta(operation.schedule_config_json)
        if latest_execution is None:
            return SchedulerDecision(True, "no previous execution")
        if latest_execution.created_at <= current_time - delta:
            return SchedulerDecision(True, "interval reached")
        return SchedulerDecision(False, "interval not reached")

    if operation.schedule_type == "cron":
        expression = (operation.schedule_config_json or {}).get("expression", "")
        if not expression:
            return SchedulerDecision(False, "missing cron expression")
        if not _matches_cron(expression, current_time):
            return SchedulerDecision(False, "cron does not match current time")
        if latest_execution and latest_execution.created_at.replace(second=0, microsecond=0) == current_time.replace(
            second=0, microsecond=0
        ):
            return SchedulerDecision(False, "already launched in current cron window")
        return SchedulerDecision(True, "cron matched")

    return SchedulerDecision(False, "unsupported schedule type")


def run_scheduler_cycle(db: Session, now: datetime | None = None) -> SchedulerRunResponse:
    current_time = now or datetime.utcnow()
    operations = db.scalars(select(Operation).order_by(Operation.id.asc())).all()
    launched_execution_ids: list[int] = []

    for operation in operations:
        decision = should_run_operation(db, operation, current_time)
        if not decision.should_run:
            continue
        execution, _task_executions = launch_operation(
            db,
            operation.id,
            OperationLaunchRequest(
                trigger_type=operation.schedule_type,
                shared_input=(operation.schedule_config_json or {}).get("shared_input"),
            ),
        )
        launched_execution_ids.append(execution.id)

    return SchedulerRunResponse(
        checked_operations=len(operations),
        launched_operations=len(launched_execution_ids),
        launched_execution_ids=launched_execution_ids,
        run_started_at=current_time,
    )


class SchedulerLoop:
    def __init__(self, poll_seconds: int) -> None:
        self.poll_seconds = max(5, poll_seconds)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="hlt-scheduler-loop", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            db = SessionLocal()
            try:
                run_scheduler_cycle(db)
            finally:
                db.close()
            self._stop_event.wait(self.poll_seconds)
