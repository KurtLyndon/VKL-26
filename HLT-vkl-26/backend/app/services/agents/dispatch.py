import httpx

from app.core.config import get_settings
from app.models import Agent, TaskExecution
from app.services.agents.runner_registry import get_runner

settings = get_settings()


def _agent_endpoint(agent: Agent) -> str | None:
    host = agent.host or agent.ip_address
    if not host:
        return None
    port = agent.port or 8001
    return f"http://{host}:{port}/execute"


def _dispatch_http(agent: Agent, task_execution: TaskExecution, target_value: str) -> tuple[str, dict]:
    endpoint = _agent_endpoint(agent)
    if not endpoint:
        raise ValueError("Agent endpoint is not configured.")

    payload = {
        "task_execution_id": task_execution.id,
        "task_id": task_execution.task_id,
        "task_code": task_execution.task.code,
        "agent_type": task_execution.task.agent_type,
        "script_name": task_execution.task.script_name,
        "script_path": task_execution.task.script_path,
        "input_data": task_execution.input_data_json or {},
        "target": target_value,
    }

    with httpx.Client(timeout=settings.agent_request_timeout_seconds) as client:
        response = client.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()

    raw_output = data.get("raw_output")
    if not raw_output:
        raise ValueError("Agent response did not include raw_output.")

    return raw_output, {
        "mode": "http-agent",
        "endpoint": endpoint,
        "response_meta": data.get("meta", {}),
    }


def dispatch_task_to_agent(agent: Agent, task_execution: TaskExecution, target_value: str) -> tuple[str, dict]:
    mode = settings.agent_dispatch_mode.lower()

    if mode in {"auto", "http"}:
        try:
            return _dispatch_http(agent, task_execution, target_value)
        except Exception:
            if mode == "http":
                raise

    runner = get_runner(task_execution.task.agent_type)
    return runner.run(task_execution, target_value), {"mode": "mock-runner"}
