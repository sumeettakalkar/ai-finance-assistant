from openai import OpenAI
from src.agents.base import AgentResponse

DISCLAIMER = (
    "Educational only — not financial advice. "
    "Consider a licensed financial professional for personalized guidance."
)

class FinanceQAAgent:
    
    name : str = "FinanceQA_Agent"
    
    def __init__(self, model: str = "gpt-5"):
        self.client = OpenAI()
        self.model = model

    def run(self, user_message: str) -> AgentResponse:
        instructions = (
            "You are a helpful finance tutor for beginners. "
            "Use simple language, define jargon, and give 1 short example. "
            "Avoid giving specific buy/sell recommendations. "
            f"Always include this disclaimer at the end: {DISCLAIMER}"
        )
        resp = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=user_message,
        )
        answer = resp.output_text.strip()
        
        return AgentResponse(
            answer=answer,
            agent_name=self.name,
            confidence="medium",
            sources=None,
        )
    