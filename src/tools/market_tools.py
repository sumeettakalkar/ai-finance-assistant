"""Pure market data functions extracted from MarketAnalysisAgent.

Functions handle ticker extraction, yfinance data fetching, and formatting.
The TTL cache integration is provided via ``get_market_data()`` which
accepts an optional cache instance.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

import yfinance as yf

from src.utils.cache import TTLCache

DISCLAIMER = (
    "Educational only — not financial advice. Market data may be delayed or incomplete."
)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def extract_ticker(message: str) -> Optional[str]:
    """Return the first token that looks like a ticker.

    Normalizes to uppercase and allows 1-5 alphanumeric characters,
    optionally prefixed with a ``$``.
    """
    match = re.search(r"\$?([A-Za-z0-9]{1,5})", message)
    if not match:
        return None
    return match.group(1).upper()


def get_quote_and_history(ticker: str, session=None) -> Optional[Dict[str, object]]:
    """Fetch current price and recent closes for ``ticker``.

    Returns a dictionary with:
        - ``price``: latest price (fast_info if available, otherwise last close)
        - ``day_change_pct``: best-effort % change vs previous close
        - ``last_5_closes``: list of recent close prices (up to 5)
    """
    try:
        if session is None:
            ticker_obj = yf.Ticker(ticker)
        else:
            ticker_obj = yf.Ticker(ticker, session=session)

        fast_info = getattr(ticker_obj, "fast_info", {}) or {}
        price = (
            fast_info.get("last_price")
            or fast_info.get("lastPrice")
            or fast_info.get("lastTradePrice")
        )

        history_df = ticker_obj.history(period="7d")

        closes: List[float] = []
        if history_df is not None and not history_df.empty and "Close" in history_df:
            closes = [float(c) for c in history_df["Close"].dropna().tolist()]
        last_5_closes: List[float] = closes[-5:]

        if price is None and last_5_closes:
            price = last_5_closes[-1]

        day_change_pct: Optional[float] = None
        if len(last_5_closes) >= 2 and last_5_closes[-2] != 0:
            latest = last_5_closes[-1]
            prev = last_5_closes[-2]
            day_change_pct = round(((latest - prev) / prev) * 100, 2)

        if price is None:
            return None

        return {
            "price": round(float(price), 2),
            "day_change_pct": day_change_pct,
            "last_5_closes": [round(float(c), 2) for c in last_5_closes],
        }

    except Exception as e:
        print(f"Failed to fetch data for ticker: {ticker}: {e}")
        return None


def get_market_data(
    ticker: str,
    cache: Optional[TTLCache] = None,
    session=None,
) -> Optional[Dict[str, object]]:
    """Cache-aware wrapper around ``get_quote_and_history``.

    If a cache is provided and the ticker is cached, returns the cached
    value. Otherwise fetches fresh data and caches it.
    """
    if cache is not None:
        cached = cache.get(ticker)
        if cached is not None:
            return cached

    data = get_quote_and_history(ticker, session=session)

    if data is not None and cache is not None:
        cache.set(ticker, data)

    return data


def format_market_report(
    ticker: str,
    data: Dict[str, object],
    cached: bool = False,
) -> str:
    """Render a human-friendly summary for the user."""
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
