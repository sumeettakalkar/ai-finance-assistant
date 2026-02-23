from dataclasses import dataclass, field
from typing import Protocol

@dataclass
class AgentResponse:
    answer: str
    agent_name: str
    confidence: str = "medium" # low, high, medium
    sources:list[str] | None= None
    metadata: dict | None = None  # Structured data for charts (Phase 4)

class Agent(Protocol):
    name: str
    def run(self, query: str) -> AgentResponse:
        ...
