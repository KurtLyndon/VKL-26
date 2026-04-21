from fastapi import HTTPException, status

from app.services.agents.base import AgentParser
from app.services.agents.nmap.parser import NmapParser
from app.services.agents.nuclei.parser import NucleiParser

PARSER_REGISTRY: dict[str, AgentParser] = {
    "nmap": NmapParser(),
    "nuclei": NucleiParser(),
}


def get_parser(agent_type: str) -> AgentParser:
    parser = PARSER_REGISTRY.get(agent_type.lower())
    if not parser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parser for agent type '{agent_type}' is not registered",
        )
    return parser
