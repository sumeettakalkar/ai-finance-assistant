from __future__ import annotations

import json
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from src.workflow.graph import get_graph
from src.storage.conversation_db import ConversationDB

app = FastAPI(
    title="AI Finance Assistant",
    description=(
        "Multi-agent finance assistant powered by LangGraph and OpenAI. "
        "Routes questions to specialist agents: Finance Q&A (RAG), "
        "Market Analysis, Portfolio Analysis, and Goal Planning."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_conversation_db = ConversationDB()


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


class NaturalLanguageRequest(BaseModel):
    description: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"description": "I have $5000 in Apple, $8000 in VTI, and $2000 in bonds"}
            ]
        }
    }


class ImageRequest(BaseModel):
    image_base64: str

    model_config = {
        "json_schema_extra": {
            "examples": [{"image_base64": "iVBORw0KGgo..."}]
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
    metadata: Optional[dict] = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    tab: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[List[str]] = None
    metadata: Optional[dict] = None
    created_at: str
    seq: int


class ConversationDetail(BaseModel):
    id: str
    title: str
    tab: str
    created_at: str
    updated_at: str
    messages: List[MessageResponse]


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
        metadata=result.get("metadata") or {},
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

    Pass a map of ticker -> dollar value. Returns allocation percentages,
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


# ---------------------------------------------------------------------------
# New endpoints (Phase 9)
# ---------------------------------------------------------------------------

@app.post("/api/portfolio/natural", response_model=FinanceResponse, tags=["Agents"])
def portfolio_natural(request: NaturalLanguageRequest):
    """
    Analyze portfolio from a natural language description.

    Example: "I have $5000 in Apple, $8000 in VTI, and $2000 in bonds"
    """
    from src.tools.parsing_tools import parse_portfolio_from_text
    result = parse_portfolio_from_text(request.description)
    if isinstance(result, str):
        raise HTTPException(status_code=422, detail=result)
    query = json.dumps(result)
    return _invoke(query, route="portfolio")


@app.post("/api/portfolio/image", response_model=FinanceResponse, tags=["Agents"])
def portfolio_image(request: ImageRequest):
    """
    Analyze portfolio from a brokerage screenshot (base64-encoded image).
    """
    from src.tools.parsing_tools import parse_portfolio_from_image
    result = parse_portfolio_from_image(request.image_base64)
    if isinstance(result, str):
        raise HTTPException(status_code=422, detail=result)
    query = json.dumps(result)
    return _invoke(query, route="portfolio")


@app.post("/api/goals/natural", response_model=FinanceResponse, tags=["Agents"])
def goals_natural(request: NaturalLanguageRequest):
    """
    Calculate savings goal from a natural language description.

    Example: "I want to save $1 million in 20 years with 7% return"
    """
    from src.tools.parsing_tools import parse_goal_from_text
    result = parse_goal_from_text(request.description)
    if isinstance(result, str):
        raise HTTPException(status_code=422, detail=result)
    query = json.dumps(result)
    return _invoke(query, route="goal")


@app.get(
    "/api/conversations",
    response_model=List[ConversationSummary],
    tags=["Conversations"],
)
def list_conversations(tab: Optional[str] = None, limit: int = 50):
    """List conversation history, optionally filtered by tab."""
    conversations = _conversation_db.list_conversations(tab=tab, limit=limit)
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            tab=c.tab,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in conversations
    ]


@app.get(
    "/api/conversations/{conv_id}",
    response_model=ConversationDetail,
    tags=["Conversations"],
)
def get_conversation(conv_id: str):
    """Get a conversation with all its messages."""
    conv = _conversation_db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        tab=conv.tab,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                metadata=m.metadata,
                created_at=m.created_at.isoformat(),
                seq=m.seq,
            )
            for m in conv.messages
        ],
    )
