from __future__ import annotations
from dataclasses import dataclass, field
from functools import lru_cache
import re
from typing import Any, Dict, List, Literal, Optional, Tuple

from langgraph.graph import END, StateGraph

from src.agents.base import AgentResponse
from src.agents.goal_agent import GoalAgent
from src.agents.market_agent import MarketAnalysisAgent
from src.agents.portfolio_agent import PortfolioAgent
from src.agents.finance_qa_agent import FinanceQAAgent

Route = Literal["goal", "market", "portfolio", "finance_qa"]

@dataclass
class GraphState:
    """State of the workflow graph, tracking conversation history and agent responses."""
    userMsg: str = ""
    route: Route | None = None
    answer: str = ""
    agent_name: str = ""
    confidence: str = ""
    sources: List[str] = field(default_factory=list)
    history: List[Tuple[str, AgentResponse]] = field(default_factory=list)
    # You can add more fields here if needed for context or intermediate data.  

def classify_route(user_message: str) -> Route:
    """Simple keyword-based routing logic to determine which agent to use."""
    msg = user_message.lower()

    # Fast path for ticker-only input (e.g., "AAPL" or "$TSLA").
    if re.fullmatch(r"\s*\$?[A-Za-z]{1,5}\s*", user_message):
        print("Routing to MarketAnalysisAgent")
        return "market"

    if "save" in msg or "goal" in msg or "expected_annual_return" in msg or "target_amount" in msg:
        print("Routing to GoalAgent")
        return "goal"
    elif "stock" in msg or "price" in msg or "market" in msg or "quote" in msg:
        print("Routing to MarketAnalysisAgent")
        return "market"
    elif "portfolio" in msg or "allocation" in msg or "diversification" in msg or "{" in msg:
        print("Routing to PortfolioAgent")
        return "portfolio"
    else:
        print("Routing to FinanceQAAgent")
        return "finance_qa"
    

@lru_cache(maxsize=1)
def _finance_agent() -> FinanceQAAgent:
    return FinanceQAAgent()

@lru_cache(maxsize=1)
def _market_agent() -> MarketAnalysisAgent:
    return MarketAnalysisAgent()

@lru_cache(maxsize=1)
def _portfolio_agent() -> PortfolioAgent:
    return PortfolioAgent()

@lru_cache(maxsize=1)
def _goal_agent() -> GoalAgent:
    return GoalAgent()

def router_node(state: GraphState) -> Dict[str, Any]:
    """Node to classify the route based on user message."""
    if state.route in ("goal", "market", "portfolio", "finance_qa"):
        return {"route": state.route}

    route = classify_route(state.userMsg)
    return {"route": route}

def finance_qa_node(state: GraphState) -> Dict[str, Any]:
    """Node to run the FinanceQAAgent."""
    response = _finance_agent().run(state.userMsg)
    return {
        "answer": response.answer,
        "agent_name": response.agent_name,
        "confidence": response.confidence,
        "sources": response.sources,
    }

def market_node(state: GraphState) -> Dict[str, Any]:
    """Node to run the MarketAnalysisAgent."""
    response = _market_agent().run(state.userMsg)
    return {
        "answer": response.answer,
        "agent_name": response.agent_name,
        "confidence": response.confidence,
        "sources": response.sources,
    }
    
def portfolio_node(state: GraphState) -> Dict[str, Any]:
    """Node to run the PortfolioAgent."""
    response = _portfolio_agent().run(state.userMsg)
    return {
        "answer": response.answer,
        "agent_name": response.agent_name,
        "confidence": response.confidence,
        "sources": response.sources,
    }
    
def goal_node(state: GraphState) -> Dict[str, Any]:
    """Node to run the GoalAgent."""
    response = _goal_agent().run(state.userMsg)
    return {
        "answer": response.answer,
        "agent_name": response.agent_name,
        "confidence": response.confidence,
        "sources": response.sources,
    }
    
#-- Graph Construction --#
def build_graph():
    graph = StateGraph(GraphState)
    
    # Define nodes
    graph.add_node("router", router_node)
    graph.add_node("finance_qa", finance_qa_node)
    graph.add_node("market", market_node)
    graph.add_node("portfolio", portfolio_node)
    graph.add_node("goal", goal_node)
    
    # Entry point and conditional routing based on route
    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        lambda state: state.route,
        {
            "finance_qa": "finance_qa",
            "market": "market",
            "portfolio": "portfolio",
            "goal": "goal",
        },
    )
    
    # End node after agent response
    graph.add_edge("finance_qa", END)
    graph.add_edge("market", END)
    graph.add_edge("portfolio", END)
    graph.add_edge("goal", END)
    
    return graph.compile()

@lru_cache(maxsize=1)
def get_graph():
    return build_graph()
