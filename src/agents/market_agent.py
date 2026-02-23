"""Market data helper agent.

This agent keeps a small time-boxed cache so we do not hit the network
for the same ticker repeatedly. The workflow is intentionally explicit
and heavily commented to make it easy to follow and extend.
"""

from __future__ import annotations

from typing import Dict, Optional

from src.agents.base import AgentResponse
from src.utils.cache import TTLCache
from src.tools.market_tools import (
    DISCLAIMER,
    extract_ticker,
    get_market_data,
    format_market_report,
)


class MarketAnalysisAgent:
    """Lightweight market lookup agent with a TTL cache."""

    # Public name used by the router / orchestrator
    name: str = "marketanalysisagent"

    def __init__(self, ttl: int = 1800, session=None):
        """Create a cache with the provided time-to-live.

        Parameters
        ----------
        ttl : int, default 1800
            Cache duration in seconds (30 minutes).
        """
        self.cache = TTLCache(ttl=ttl)
        self._session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, user_message: str) -> AgentResponse:
        """Handle a user request and return an AgentResponse."""

        ticker = self._extract_ticker(user_message)

        if not ticker:
            return AgentResponse(
                answer=self._with_disclaimer(
                    "I couldn't spot a ticker symbol in your message."
                ),
                agent_name=self.name,
                confidence="low",
                sources=[],
            )

        market_data = get_market_data(
            ticker, cache=self.cache, session=self._session,
        )

        if market_data is None:
            return AgentResponse(
                answer=self._with_disclaimer(
                    f"I couldn't fetch data for {ticker} right now."
                ),
                agent_name=self.name,
                confidence="low",
                sources=["yfinance"],
            )

        # Check if this came from cache (cache.get would have returned it)
        cached = self.cache.get(ticker) is not None
        formatted = format_market_report(ticker, market_data, cached=cached)
        return AgentResponse(
            answer=self._with_disclaimer(formatted),
            agent_name=self.name,
            confidence="high",
            sources=["yfinance (cache)" if cached else "yfinance"],
        )

    # ------------------------------------------------------------------
    # Helper methods (delegate to tools, preserve private API for tests)
    # ------------------------------------------------------------------
    def _extract_ticker(self, message: str) -> Optional[str]:
        """Return the first token that looks like a ticker."""
        return extract_ticker(message)

    def _get_quote_and_history(self, ticker: str) -> Optional[Dict[str, object]]:
        """Fetch current price and recent closes for ``ticker``."""
        from src.tools.market_tools import get_quote_and_history
        return get_quote_and_history(ticker, session=self._session)

    def _format_answer(self, ticker: str, data: Dict[str, object], cached: bool = False) -> str:
        """Render a human-friendly summary for the user."""
        return format_market_report(ticker, data, cached=cached)

    def _with_disclaimer(self, message: str) -> str:
        if "disclaimer:" in message.lower():
            return message
        return f"{message}\n\nDisclaimer: {DISCLAIMER}"
