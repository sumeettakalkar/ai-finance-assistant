"""MCP server exposing finance tools to Claude Desktop and other MCP clients.

Run directly:
    python -m src.mcp.server

Or configure in Claude Desktop's ``claude_desktop_config.json``::

    {
      "mcpServers": {
        "ai-finance-assistant": {
          "command": "python",
          "args": ["-m", "src.mcp.server"],
          "cwd": "/path/to/ai-finance-assistant",
          "env": { "OPENAI_API_KEY": "sk-..." }
        }
      }
    }
"""

from __future__ import annotations

import json
from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.tools.portfolio_tools import (
    sanitize_holdings,
    compute_portfolio_metrics,
    format_portfolio_report,
)
from src.tools.goal_tools import (
    validate_and_normalize_goal,
    compute_monthly_contribution,
    format_goal_report,
)
from src.tools.market_tools import (
    extract_ticker,
    get_market_data,
    format_market_report,
)

mcp = FastMCP("ai-finance-assistant")


# ---------------------------------------------------------------------------
# Portfolio tools
# ---------------------------------------------------------------------------

@mcp.tool()
def analyze_portfolio(holdings: dict[str, float]) -> str:
    """Full portfolio analysis with diversification score, risk, and asset mix.

    Parameters
    ----------
    holdings : dict
        Mapping of ticker symbol to dollar value, e.g. {"AAPL": 5000, "VTI": 8000}.

    Returns
    -------
    str
        A markdown report with allocation breakdown, risk level, and asset mix.
    """
    clean = sanitize_holdings(holdings)
    if not clean:
        return "No usable holdings found. Provide positive dollar amounts per ticker."
    metrics = compute_portfolio_metrics(clean)
    return format_portfolio_report(metrics)


@mcp.tool()
def compute_portfolio_risk(holdings: dict[str, float]) -> dict:
    """Machine-readable portfolio metrics including risk, diversification, and asset mix.

    Parameters
    ----------
    holdings : dict
        Mapping of ticker symbol to dollar value.

    Returns
    -------
    dict
        Raw metrics dict with keys: total, allocations, diversification_score,
        risk, triggers, stock_pct, bond_pct, other_pct.
    """
    clean = sanitize_holdings(holdings)
    if not clean:
        return {"error": "No usable holdings found."}
    return compute_portfolio_metrics(clean)


# ---------------------------------------------------------------------------
# Goal planning tools
# ---------------------------------------------------------------------------

@mcp.tool()
def plan_savings_goal(
    target_amount: float,
    years: float,
    expected_annual_return: float,
    current_savings: float = 0.0,
) -> str:
    """Calculate monthly savings needed to reach a financial goal.

    Uses future-value / ordinary-annuity math. Accepts annual return as
    either decimal (0.07) or percent (7).

    Parameters
    ----------
    target_amount : float
        The target dollar amount to reach.
    years : float
        Number of years to reach the goal.
    expected_annual_return : float
        Expected annual return (0.07 or 7 both mean 7%).
    current_savings : float
        Amount already saved (default 0).

    Returns
    -------
    str
        A markdown report with required monthly contribution and details.
    """
    payload = {
        "target_amount": target_amount,
        "years": years,
        "expected_annual_return": expected_annual_return,
        "current_savings": current_savings,
    }
    normalized = validate_and_normalize_goal(payload)
    if isinstance(normalized, str):
        return f"Error: {normalized}"
    result = compute_monthly_contribution(normalized)
    return format_goal_report(result)


# ---------------------------------------------------------------------------
# Market tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_stock_quote(ticker: str) -> str:
    """Get current stock price, last 5 closes, and day change percentage.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol (e.g. "AAPL", "TSLA").

    Returns
    -------
    str
        Formatted string with price, change, and recent closes.
    """
    clean_ticker = extract_ticker(ticker)
    if not clean_ticker:
        return f"Could not parse ticker from: {ticker}"

    data = get_market_data(clean_ticker)
    if data is None:
        return f"Could not fetch data for {clean_ticker}."

    return format_market_report(clean_ticker, data)


# ---------------------------------------------------------------------------
# RAG tools
# ---------------------------------------------------------------------------

@mcp.tool()
def search_finance_knowledge(query: str, top_k: int = 5) -> list[str]:
    """Search the finance knowledge base using RAG.

    Queries the FAISS vector store over the built-in finance articles
    (diversification, stocks, bonds, ETFs, asset allocation, three-fund
    portfolio).

    Parameters
    ----------
    query : str
        Natural language question to search for.
    top_k : int
        Number of relevant chunks to return (default 5).

    Returns
    -------
    list[str]
        The most relevant text chunks from the knowledge base.
    """
    from src.tools.rag_tools import retrieve_finance_context
    return retrieve_finance_context(query, top_k=top_k)


# ---------------------------------------------------------------------------
# NL parsing tools (convenience wrappers — full parsing in Phase 3)
# ---------------------------------------------------------------------------

@mcp.tool()
def parse_portfolio_description(description: str) -> str:
    """Parse a natural language portfolio description and analyze it.

    Accepts free-text like "I have $5000 in Apple, $8000 in VTI" and
    attempts to extract holdings, then runs full portfolio analysis.

    Parameters
    ----------
    description : str
        Natural language description of portfolio holdings.

    Returns
    -------
    str
        Markdown portfolio analysis report, or error message.
    """
    # Try JSON first (backward compatible)
    try:
        holdings = json.loads(description)
        if isinstance(holdings, dict):
            return analyze_portfolio(holdings)
    except (json.JSONDecodeError, TypeError):
        pass

    # Defer to NL parsing (available after Phase 3)
    try:
        from src.tools.parsing_tools import parse_portfolio_from_text
        result = parse_portfolio_from_text(description)
        if isinstance(result, dict):
            return analyze_portfolio(result)
        return f"Could not parse portfolio: {result}"
    except ImportError:
        return (
            "Natural language parsing not yet available. "
            "Please provide JSON like {\"AAPL\": 5000, \"VTI\": 8000}."
        )


@mcp.tool()
def parse_goal_description(description: str) -> str:
    """Parse a natural language goal description and calculate savings plan.

    Accepts free-text like "I want to save $1M in 20 years with 7% return"
    and extracts goal parameters, then computes monthly contribution.

    Parameters
    ----------
    description : str
        Natural language description of savings goal.

    Returns
    -------
    str
        Markdown goal plan report, or error message.
    """
    # Try JSON first (backward compatible)
    try:
        payload = json.loads(description)
        if isinstance(payload, dict):
            normalized = validate_and_normalize_goal(payload)
            if isinstance(normalized, str):
                return f"Error: {normalized}"
            result = compute_monthly_contribution(normalized)
            return format_goal_report(result)
    except (json.JSONDecodeError, TypeError):
        pass

    # Defer to NL parsing (available after Phase 3)
    try:
        from src.tools.parsing_tools import parse_goal_from_text
        result = parse_goal_from_text(description)
        if isinstance(result, dict):
            normalized = validate_and_normalize_goal(result)
            if isinstance(normalized, str):
                return f"Error: {normalized}"
            computed = compute_monthly_contribution(normalized)
            return format_goal_report(computed)
        return f"Could not parse goal: {result}"
    except ImportError:
        return (
            "Natural language parsing not yet available. "
            'Please provide JSON like {"target_amount": 1000000, "years": 20, '
            '"expected_annual_return": 7}.'
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
