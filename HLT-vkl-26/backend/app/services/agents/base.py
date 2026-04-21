from abc import ABC, abstractmethod


class AgentParser(ABC):
    agent_type: str

    @abstractmethod
    def normalize(self, raw_output: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def extract_findings(self, raw_output: str) -> list[dict]:
        raise NotImplementedError
