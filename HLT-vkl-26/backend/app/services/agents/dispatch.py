import httpx

from app.core.config import get_settings
from app.models import Agent, Target, TaskExecution
from app.services.agent_runtime import build_execute_request, parse_execute_response
from app.services.agents.runner_registry import get_runner

settings = get_settings()


def _agent_endpoint(agent: Agent) -> str | None:
    host = agent.host or agent.ip_address
    if not host:
        return None
    port = agent.port or 8001
    return f"http://{host}:{port}/execute"


def _dispatch_http(
    agent: Agent, task_execution: TaskExecution, target_value: str, target: Target | None = None
) -> tuple[str | None, dict]:
    endpoint = _agent_endpoint(agent)
    if not endpoint:
        raise ValueError("Agent endpoint is not configured.")

    payload = build_execute_request(agent, task_execution, target, target_value).model_dump(mode="json")

    with httpx.Client(timeout=settings.agent_request_timeout_seconds) as client:
        response = client.post(endpoint, json=payload)
        response.raise_for_status()
        data = response.json()

    raw_output, output_data, response_meta = parse_execute_response(data)

    return raw_output, {
        "mode": "http-agent",
        "endpoint": endpoint,
        "contract_version": data.get("contract_version"),
        **output_data,
        "response_meta": response_meta,
    }


def dispatch_task_to_agent(
    agent: Agent, task_execution: TaskExecution, target_value: str, target: Target | None = None
) -> tuple[str | None, dict]:
    mode = settings.agent_dispatch_mode.lower()

    if mode in {"auto", "http"}:
        try:
            return _dispatch_http(agent, task_execution, target_value, target)
        except Exception:
            if mode == "http":
                raise

    runner = get_runner(task_execution.task.agent_type)
    return runner.run(task_execution, target_value), {"mode": "mock-runner"}
