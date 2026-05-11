from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Agent, Operation, OperationExecution, Task, TaskExecution
from app.schemas.resources import AgentMonitorCardRead, AgentMonitorOverviewResponse, AgentMonitorRunResponse, AgentTypeSummary

settings = get_settings()

READY_STATUS = "ready"
WORKING_STATUS = "working"
ERROR_STATUS = "error"
OFFLINE_STATUS = "offline"
MONITORED_STATUSES = {READY_STATUS, WORKING_STATUS, ERROR_STATUS, OFFLINE_STATUS}
STATUS_PRIORITY = {READY_STATUS: 0, WORKING_STATUS: 1, ERROR_STATUS: 2, OFFLINE_STATUS: 3}
SYSTEM_PRIORITY = {"system": 0}
DEFAULT_READY_NOTE = "Sẵn sàng"
DEFAULT_OFFLINE_NOTE = "Đang thử kết nối lại..."

_last_run_at: datetime | None = None


@dataclass
class AgentRuntimeSnapshot:
    status: str
    status_note: str
    task_execution_count: int
    operation_execution_count: int


def normalize_agent_status(raw_status: str | None) -> str:
    value = (raw_status or "").strip().lower()
    if value in {"online", "idle", "available", READY_STATUS}:
        return READY_STATUS
    if value in {"running", WORKING_STATUS}:
        return WORKING_STATUS
    if value in {"failed", ERROR_STATUS}:
        return ERROR_STATUS
    if value in {"offline", "disconnected"}:
        return OFFLINE_STATUS
    return READY_STATUS if value else OFFLINE_STATUS


def format_duration(seconds: int | None) -> str:
    total_seconds = max(int(seconds or 0), 0)
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days} ngày")
    if hours or days:
        parts.append(f"{hours} giờ")
    parts.append(f"{minutes} phút")
    return " ".join(parts)


def _health_endpoint(agent: Agent) -> str | None:
    host = agent.host or agent.ip_address
    if not host or not agent.port:
        return None
    return f"http://{host}:{agent.port}/health"


def _should_treat_as_internal(agent: Agent) -> bool:
    if agent.agent_type == "system":
        return True
    if (agent.host or "").lower() == "localhost" and (agent.ip_address in {None, "", "127.0.0.1"}):
        return True
    return False


def _is_agent_connected(agent: Agent, now: datetime) -> bool:
    if _should_treat_as_internal(agent):
        return True
    endpoint = _health_endpoint(agent)
    if not endpoint:
        return False
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(endpoint)
            if response.status_code < 400:
                return True
    except Exception:
        return False

    stale_seconds = max(settings.agent_status_stale_seconds, settings.agent_monitor_poll_seconds)
    if agent.last_seen_at is None:
        return False
    return (now - agent.last_seen_at) <= timedelta(seconds=stale_seconds)


def _running_task_context(db: Session, agent_id: int) -> tuple[str, str] | None:
    row = db.execute(
        select(TaskExecution, Task, OperationExecution, Operation)
        .join(Task, Task.id == TaskExecution.task_id)
        .join(OperationExecution, OperationExecution.id == TaskExecution.operation_execution_id)
        .join(Operation, Operation.id == OperationExecution.operation_id)
        .where(TaskExecution.agent_id == agent_id)
        .where(TaskExecution.status == "running")
        .order_by(TaskExecution.started_at.desc(), TaskExecution.id.desc())
        .limit(1)
    ).first()
    if not row:
        return None
    task_execution, task, operation_execution, operation = row
    note = f"{operation.name} / {task.name}"
    return WORKING_STATUS, note


def _count_task_executions(db: Session, agent_id: int) -> int:
    return db.scalar(select(func.count(TaskExecution.id)).where(TaskExecution.agent_id == agent_id)) or 0


def _count_operation_executions(db: Session, agent_id: int) -> int:
    return (
        db.scalar(
            select(func.count(func.distinct(TaskExecution.operation_execution_id))).where(TaskExecution.agent_id == agent_id)
        )
        or 0
    )


def _apply_status_window(agent: Agent, next_status: str, next_note: str, now: datetime) -> None:
    normalized_next = normalize_agent_status(next_status)
    normalized_old = normalize_agent_status(agent.old_status or agent.status or OFFLINE_STATUS)
    if agent.old_time is None:
        agent.old_time = now
    if normalized_old != normalized_next:
        agent.old_status = normalized_next
        agent.old_time = now
        agent.duration = 0
    else:
        agent.duration = max(int((now - agent.old_time).total_seconds()), 0)
        agent.old_status = normalized_next

    agent.status = normalized_next
    agent.status_note = next_note


def compute_agent_snapshot(db: Session, agent: Agent, now: datetime | None = None) -> AgentRuntimeSnapshot:
    current_time = now or datetime.utcnow()
    task_execution_count = _count_task_executions(db, agent.id)
    operation_execution_count = _count_operation_executions(db, agent.id)

    running_context = _running_task_context(db, agent.id)
    if running_context:
        status_value, note = running_context
        return AgentRuntimeSnapshot(status_value, note, task_execution_count, operation_execution_count)

    connected = _is_agent_connected(agent, current_time)
    current_status = normalize_agent_status(agent.status)
    current_note = (agent.status_note or "").strip()

    if not connected:
        return AgentRuntimeSnapshot(OFFLINE_STATUS, DEFAULT_OFFLINE_NOTE, task_execution_count, operation_execution_count)
    if current_status == ERROR_STATUS:
        return AgentRuntimeSnapshot(ERROR_STATUS, current_note or "Agent đang gặp lỗi.", task_execution_count, operation_execution_count)
    return AgentRuntimeSnapshot(READY_STATUS, DEFAULT_READY_NOTE, task_execution_count, operation_execution_count)


def mark_agent_status(agent: Agent, status_value: str, status_note: str | None, when: datetime | None = None) -> None:
    current_time = when or datetime.utcnow()
    _apply_status_window(agent, status_value, status_note or DEFAULT_READY_NOTE, current_time)
    if status_value in {READY_STATUS, WORKING_STATUS, ERROR_STATUS}:
        agent.last_seen_at = current_time


def list_agent_cards(db: Session) -> list[AgentMonitorCardRead]:
    agents = db.scalars(select(Agent).order_by(Agent.id.asc())).all()
    current_time = datetime.utcnow()
    cards: list[AgentMonitorCardRead] = []
    for agent in agents:
        snapshot = compute_agent_snapshot(db, agent, current_time)
        old_status = normalize_agent_status(agent.old_status or agent.status or OFFLINE_STATUS)
        if agent.old_time and old_status == snapshot.status:
            preview_duration = max(int((current_time - agent.old_time).total_seconds()), 0)
        else:
            preview_duration = 0
        cards.append(
            AgentMonitorCardRead(
                id=agent.id,
                code=agent.code,
                name=agent.name,
                agent_type=agent.agent_type,
                host=agent.host,
                ip_address=agent.ip_address,
                port=agent.port,
                version=agent.version,
                status=snapshot.status,
                duration=preview_duration,
                duration_label=format_duration(preview_duration),
                old_time=agent.old_time,
                old_status=agent.old_status,
                status_note=snapshot.status_note,
                last_seen_at=agent.last_seen_at,
                task_execution_count=snapshot.task_execution_count,
                operation_execution_count=snapshot.operation_execution_count,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
            )
        )

    def _sort_key(item: AgentMonitorCardRead) -> tuple[int, int, str, int]:
        return (
            STATUS_PRIORITY.get(normalize_agent_status(item.status), 99),
            SYSTEM_PRIORITY.get(item.agent_type, 1),
            item.agent_type,
            item.id,
        )

    cards.sort(key=_sort_key)
    return cards


def get_agent_monitor_overview(db: Session) -> AgentMonitorOverviewResponse:
    cards = list_agent_cards(db)
    type_counts: dict[str, int] = {}
    for card in cards:
        type_counts[card.agent_type] = type_counts.get(card.agent_type, 0) + 1
    next_run_at = _last_run_at + timedelta(seconds=settings.agent_monitor_poll_seconds) if _last_run_at else None
    return AgentMonitorOverviewResponse(
        total_agents=len(cards),
        type_summaries=[AgentTypeSummary(agent_type=agent_type, count=count) for agent_type, count in sorted(type_counts.items())],
        agents=cards,
        last_run_at=_last_run_at,
        next_run_at=next_run_at,
        poll_seconds=settings.agent_monitor_poll_seconds,
    )


def run_agent_monitor_cycle(db: Session, now: datetime | None = None) -> AgentMonitorRunResponse:
    global _last_run_at
    current_time = now or datetime.utcnow()
    agents = db.scalars(select(Agent).order_by(Agent.id.asc())).all()
    ready_count = working_count = error_count = offline_count = 0

    for agent in agents:
        snapshot = compute_agent_snapshot(db, agent, current_time)
        _apply_status_window(agent, snapshot.status, snapshot.status_note, current_time)
        if snapshot.status == READY_STATUS:
            ready_count += 1
        elif snapshot.status == WORKING_STATUS:
            working_count += 1
        elif snapshot.status == ERROR_STATUS:
            error_count += 1
        else:
            offline_count += 1

    db.commit()
    _last_run_at = current_time
    next_run_at = current_time + timedelta(seconds=settings.agent_monitor_poll_seconds)
    return AgentMonitorRunResponse(
        checked_agents=len(agents),
        ready_agents=ready_count,
        working_agents=working_count,
        error_agents=error_count,
        offline_agents=offline_count,
        run_started_at=current_time,
        next_run_at=next_run_at,
    )


def should_trigger_manual_agent_monitor(now: datetime | None = None) -> bool:
    current_time = now or datetime.utcnow()
    if _last_run_at is None:
        return True
    next_run_at = _last_run_at + timedelta(seconds=settings.agent_monitor_poll_seconds)
    remaining = (next_run_at - current_time).total_seconds()
    return remaining > 10


class AgentMonitorLoop:
    def __init__(self, poll_seconds: int) -> None:
        self.poll_seconds = max(10, poll_seconds)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="hlt-agent-monitor-loop", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            db = SessionLocal()
            try:
                run_agent_monitor_cycle(db)
            finally:
                db.close()
            self._stop_event.wait(self.poll_seconds)
