from fastapi import HTTPException, status

from app.services.agents.acunetix.runner import AcunetixRunner
from app.services.agents.nmap.runner import NmapRunner
from app.services.agents.nuclei.runner import NucleiRunner
from app.services.agents.runner_base import AgentRunner

RUNNER_REGISTRY: dict[str, AgentRunner] = {
    "acunetix": AcunetixRunner(),
    "nmap": NmapRunner(),
    "nuclei": NucleiRunner(),
}


def get_runner(agent_type: str) -> AgentRunner:
    runner = RUNNER_REGISTRY.get(agent_type.lower())
    if not runner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Runner for agent type '{agent_type}' is not registered",
        )
    return runner
