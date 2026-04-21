from abc import ABC, abstractmethod

from app.models import TaskExecution


class AgentRunner(ABC):
    agent_type: str

    @abstractmethod
    def run(self, task_execution: TaskExecution, target_value: str) -> str:
        raise NotImplementedError
