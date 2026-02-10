"""Market data helper agent.

This agent keeps a small time‑boxed cache so we do not hit the network
for the same ticker repeatedly. The workflow is intentionally explicit
and heavily commented to make it easy to follow and extend.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import yfinance as yf

from src.agents.base import AgentResponse
from src.utils.cache import TTLCache

DISCLAIMER = (
    "Educational only — not financial advice. Market data may be delayed or incomplete."
)


class MarketAnalysisAgent:
    """Lightweight market lookup agent with a TTL cache."""

    # Public name used by the router / orchestrator
    name: str = "marketanalysisagent"

    def __init__(self, ttl: int = 1800, session=None):
        """Create a cache with the provided time‑to‑live.

        Parameters
        ----------
        ttl : int, default 1800
            Cache duration in seconds (30 minutes). The value is passed
            straight into ``TTLCache`` so it is easy to tune later.
        """

        # Store market lookups for ``ttl`` seconds to avoid repeat calls.
        self.cache = TTLCache(ttl=ttl)
        self._session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, user_message: str) -> AgentResponse:
        """Handle a user request and return an AgentResponse.

        The first thing we do is to extract a ticker symbol from the
        user's message. We keep this simple: grab the first token that
        looks like a stock ticker (letters/numbers, up to 5 chars).
        """

        ticker = self._extract_ticker(user_message)

        if not ticker:
            return AgentResponse(
                answer=self._with_disclaimer("I couldn't spot a ticker symbol in your message."),
                agent_name=self.name,
                confidence="low",
                sources=[],
            )

        # Normalized ticker is our cache key (prevents case mismatches).
        cached_data = self.cache.get(ticker)
        if cached_data:
            formatted = self._format_answer(ticker, cached_data, cached=True)
            return AgentResponse(
                answer=self._with_disclaimer(formatted),
                agent_name=self.name,
                confidence="high",
                sources=["yfinance (cache)"],
            )

        # Not in cache -> fetch from yfinance.
        market_data = self._get_quote_and_history(ticker)

        if market_data is None:
            return AgentResponse(
                answer=self._with_disclaimer(
                    f"I couldn't fetch data for {ticker} right now."
                ),
                agent_name=self.name,
                confidence="low",
                sources=["yfinance"],
            )

        # Save fresh data so follow‑up queries are instant.
        self.cache.set(ticker, market_data)

        formatted = self._format_answer(ticker, market_data)
        return AgentResponse(
            answer=self._with_disclaimer(formatted),
            agent_name=self.name,
            confidence="high",
            sources=["yfinance"],
        )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _extract_ticker(self, message: str) -> Optional[str]:
        """Return the first token that looks like a ticker.

        We normalize to uppercase and allow 1–5 alphanumeric characters,
        optionally prefixed with a ``$`` (common in chat). Examples that
        will match: ``AAPL``, ``$TSLA``, ``msft``.
        """

        # Grab candidate tokens; keep it simple with a regex.
        match = re.search(r"\$?([A-Za-z0-9]{1,5})", message)
        if not match:
            return None

        return match.group(1).upper()

    def _get_quote_and_history(self, ticker: str) -> Optional[Dict[str, object]]:
        """Fetch current price and recent closes for ``ticker``.

        Returns a dictionary with:
            - ``price``: latest price (fast_info if available, otherwise last close)
            - ``day_change_pct``: best‑effort % change vs previous close
            - ``last_5_closes``: list of recent close prices (up to 5)
        """

        try:
            if self._session is None:
                ticker_obj = yf.Ticker(ticker)
            else:
                ticker_obj = yf.Ticker(ticker, session=self._session)

            # Try fast_info first — it's the quickest path to the last price.
            fast_info = getattr(ticker_obj, "fast_info", {}) or {}
            price = (
                fast_info.get("last_price")
                or fast_info.get("lastPrice")
                or fast_info.get("lastTradePrice")
            )

            # Pull a small window of history; 7d typically covers 5 trading days.
            history_df = ticker_obj.history(period="7d")

            closes: List[float] = []
            if history_df is not None and not history_df.empty and "Close" in history_df:
                # Convert closes to plain floats and drop NaNs to stay defensive.
                closes = [float(c) for c in history_df["Close"].dropna().tolist()]
            last_5_closes: List[float] = closes[-5:]

            # If fast_info didn't give us a price, use the most recent close.
            if price is None and last_5_closes:
                price = last_5_closes[-1]

            # Compute day-over-day change when we have at least two closes.
            day_change_pct: Optional[float] = None
            if len(last_5_closes) >= 2 and last_5_closes[-2] != 0:
                latest = last_5_closes[-1]
                prev = last_5_closes[-2]
                day_change_pct = round(((latest - prev) / prev) * 100, 2)

            if price is None:
                # Could not determine a price; signal failure.
                return None

            return {
                "price": round(float(price), 2),
                "day_change_pct": day_change_pct,
                "last_5_closes": [round(float(c), 2) for c in last_5_closes],
            }

        except Exception as e:
            # Keep failures quiet and let the caller decide how to respond.
            # TODO : Log exceptions for monitoring.
            print(f"Failed to fetch data for ticker: {ticker}: {e}")
            return None

    def _format_answer(self, ticker: str, data: Dict[str, object], cached: bool = False) -> str:
        """Render a human‑friendly summary for the user."""

        price = data.get("price")
        day_change = data.get("day_change_pct")
        closes = data.get("last_5_closes", [])

        parts = []
        parts.append(f"{ticker}: ${price}")

        if day_change is not None:
            parts.append(f"{day_change}% vs prior close")

        if closes:
            closes_str = ", ".join([f"${c}" for c in closes])
            parts.append(f"Last 5 closes: {closes_str}")

        if cached:
            parts.append("(cached)")

        return " | ".join(parts)

    def _with_disclaimer(self, message: str) -> str:
        if "disclaimer:" in message.lower():
            return message
        return f"{message}\n\nDisclaimer: {DISCLAIMER}"
