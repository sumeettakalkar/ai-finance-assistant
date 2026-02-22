from __future__ import annotations

import json
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from src.workflow.graph import get_graph

app = FastAPI(
    title="AI Finance Assistant",
    description=(
        "Multi-agent finance assistant powered by LangGraph and OpenAI. "
        "Routes questions to specialist agents: Finance Q&A (RAG), "
        "Market Analysis, Portfolio Analysis, and Goal Planning."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    route: Optional[Literal["goal", "market", "portfolio", "finance_qa"]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"message": "What is dollar-cost averaging?"},
                {"message": "AAPL", "route": "market"},
            ]
        }
    }


class PortfolioRequest(BaseModel):
    holdings: Dict[str, float]

    model_config = {
        "json_schema_extra": {
            "examples": [{"holdings": {"AAPL": 5000, "VTI": 8000, "BND": 2000}}]
        }
    }


class GoalRequest(BaseModel):
    target_amount: float
    years: int
    expected_annual_return: float
    current_savings: float = 0.0

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "target_amount": 1000000,
                    "years": 20,
                    "expected_annual_return": 7,
                    "current_savings": 10000,
                }
            ]
        }
    }


class FinanceResponse(BaseModel):
    answer: str
    agent_name: str
    confidence: str
    sources: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _invoke(message: str, route: Optional[str] = None) -> FinanceResponse:
    payload: dict = {"userMsg": message}
    if route:
        payload["route"] = route

    result = get_graph().invoke(payload)
    return FinanceResponse(
        answer=result.get("answer", ""),
        agent_name=result.get("agent_name", ""),
        confidence=result.get("confidence", "medium"),
        sources=result.get("sources") or [],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    """Redirect root to the interactive API docs."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"])
def health():
    """Liveness check — returns 200 when the service is up."""
    return {"status": "ok"}


@app.post("/api/chat", response_model=FinanceResponse, tags=["Agents"])
def chat(request: ChatRequest):
    """
    General chat endpoint.

    Automatically routes to the best agent based on message content,
    or you can force a specific agent by setting `route`.
    """
    return _invoke(request.message, request.route)


@app.get("/api/market/{ticker}", response_model=FinanceResponse, tags=["Agents"])
def market(ticker: str):
    """
    Fetch live market data for a stock ticker.

    Example tickers: `AAPL`, `TSLA`, `VTI`.
    Results are cached for 30 minutes.
    """
    return _invoke(ticker, route="market")


@app.post("/api/portfolio", response_model=FinanceResponse, tags=["Agents"])
def portfolio(request: PortfolioRequest):
    """
    Analyze portfolio diversification and risk.

    Pass a map of ticker → dollar value. Returns allocation percentages,
    a diversification score, and a risk label.
    """
    query = json.dumps(request.holdings)
    return _invoke(query, route="portfolio")


@app.post("/api/goals", response_model=FinanceResponse, tags=["Agents"])
def goals(request: GoalRequest):
    """
    Calculate monthly savings needed to reach a financial goal.

    Uses future-value / ordinary-annuity math to compute the required
    monthly contribution.
    """
    query = json.dumps(request.model_dump())
    return _invoke(query, route="goal")
