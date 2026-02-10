import os

from openai import OpenAI
from src.agents.base import AgentResponse
from src.rag.retriever import Retriever

DISCLAIMER = (
    "Educational only — not financial advice. "
    "Consider a licensed financial professional for personalized guidance."
)

class FinanceQAAgent:
    
    name : str = "FinanceQA_Agent"
    
    def __init__(self, model: str | None = None):
        self.client = OpenAI()
        # Favor a low-latency default model for chat UX.
        self.model = model or os.getenv("OPENAI_FINANCE_MODEL", "gpt-4o-mini")
        self.retriever = Retriever()

    def run(self, user_message: str) -> AgentResponse:
        context_chunks = self.retriever.retrieve(user_message, top_k=5)
        context = "\n\n".join(context_chunks)
        instructions = (
            "You are a helpful finance tutor for beginners. "
            "Use simple language, define jargon, and give 1 short example. "
            "Answer ONLY using the context below.\n"
            "If the answer is not in the context, say you don’t know.\n\n"
            f"Context:\n{context}\n\n"
            f"Disclaimer: {DISCLAIMER}"
        )
        resp = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=user_message,
            max_output_tokens=300,
        )
        answer = self._with_disclaimer(resp.output_text.strip())
        
        return AgentResponse(
            answer=answer,
            agent_name=self.name,
            confidence="high",
            sources=["Investopedia"],
        )

    def _with_disclaimer(self, message: str) -> str:
        if "disclaimer:" in message.lower():
            return message
        return f"{message}\n\nDisclaimer: {DISCLAIMER}"
