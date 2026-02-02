from dataclasses import dataclass
from typing import Protocol

@dataclass
class AgentResponse:
    answer: str
    agent_name: str
    confidence: str = "medium" # low, high, medium
    sources:list[str] | None= None

class Agent(Protocol):
    name: str 
    def run(self, query: str) -> AgentResponse:
        ...