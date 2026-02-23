"""Reusable finance tool functions.

This package exposes pure functions extracted from agents so they can be
shared by agents, the MCP server, and the REST API without duplication.
"""

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
    get_quote_and_history,
    get_market_data,
    format_market_report,
)
from src.tools.rag_tools import retrieve_finance_context

__all__ = [
    "sanitize_holdings",
    "compute_portfolio_metrics",
    "format_portfolio_report",
    "validate_and_normalize_goal",
    "compute_monthly_contribution",
    "format_goal_report",
    "extract_ticker",
    "get_quote_and_history",
    "get_market_data",
    "format_market_report",
    "retrieve_finance_context",
]
