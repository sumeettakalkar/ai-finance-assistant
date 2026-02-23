"""Natural language parsing tools using OpenAI function calling.

Converts free-text descriptions into the structured JSON that agents
already understand. Also supports image-to-JSON via GPT-4o Vision.
"""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


def _get_client() -> OpenAI:
    return OpenAI()


def _get_model() -> str:
    return os.getenv("OPENAI_FINANCE_MODEL", "gpt-4o-mini")


# ---------------------------------------------------------------------------
# Portfolio parsing
# ---------------------------------------------------------------------------

_PORTFOLIO_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_portfolio",
        "description": (
            "Extract stock/ETF/bond ticker symbols and their dollar amounts "
            "from a portfolio description. Always return at least one holding "
            "if dollar amounts are mentioned."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "holdings": {
                    "type": "array",
                    "description": "List of holdings with ticker and dollar amount.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "Uppercase ticker symbol (e.g. AAPL, VTI, BND)",
                            },
                            "amount": {
                                "type": "number",
                                "description": "Dollar value of the holding",
                            },
                        },
                        "required": ["ticker", "amount"],
                    },
                }
            },
            "required": ["holdings"],
        },
    },
}

_PORTFOLIO_SYSTEM_PROMPT = (
    "You are a portfolio parser. Extract stock ticker symbols and dollar amounts "
    "from the user's description.\n\n"
    "Rules:\n"
    "- Map company names to their standard NYSE/NASDAQ ticker symbols:\n"
    "  Apple → AAPL, Microsoft → MSFT, Google → GOOGL, Amazon → AMZN,\n"
    "  Tesla → TSLA, Nvidia → NVDA, Meta → META\n"
    "- Map fund/ETF names to tickers:\n"
    "  Vanguard Total Stock Market → VTI, S&P 500 index → VOO or SPY\n"
    "- Map generic asset classes to common ETF tickers:\n"
    "  bonds → BND, international stocks → VXUS, total bond market → BND,\n"
    "  treasury bonds → TLT, aggregate bonds → AGG\n"
    "- Convert shorthand amounts: $5k → 5000, $1M → 1000000\n"
    "- Numbers without $ are treated as dollar amounts\n"
    "- Always use UPPERCASE ticker symbols\n\n"
    "Example input: 'I have 5000 in Apple, 8000 in VTI, and $2000 in bonds'\n"
    "Example output: {\"AAPL\": 5000, \"VTI\": 8000, \"BND\": 2000}"
)


def parse_portfolio_from_text(text: str) -> dict | str:
    """Parse a natural language portfolio description into {ticker: dollars}.

    If the input is already valid JSON, it is returned directly (backward
    compatible). Otherwise, OpenAI function calling extracts holdings.

    Returns
    -------
    dict
        Parsed holdings like {"AAPL": 5000, "VTI": 8000} on success.
    str
        Error message on failure.
    """
    # Fast path: already JSON
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_get_model(),
            messages=[
                {"role": "system", "content": _PORTFOLIO_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            tools=[_PORTFOLIO_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_portfolio"}},
        )
        tool_call = response.choices[0].message.tool_calls[0]
        raw_args = tool_call.function.arguments
        args = json.loads(raw_args)

        # Convert array format [{ticker, amount}, ...] to dict {ticker: amount}
        raw_holdings = args.get("holdings", [])
        if isinstance(raw_holdings, list):
            holdings = {}
            for item in raw_holdings:
                if isinstance(item, dict) and "ticker" in item and "amount" in item:
                    ticker = str(item["ticker"]).upper().strip()
                    holdings[ticker] = float(item["amount"])
        elif isinstance(raw_holdings, dict):
            # Fallback: model returned dict format directly
            holdings = raw_holdings
        else:
            holdings = {}

        if not holdings:
            return (
                f"Could not extract any holdings from the description. "
                f"Model returned: {raw_args}"
            )
        return holdings
    except Exception as e:
        return f"Failed to parse portfolio description: {e}"


# ---------------------------------------------------------------------------
# Goal parsing
# ---------------------------------------------------------------------------

_GOAL_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_goal",
        "description": "Extract savings goal parameters from a natural language description.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_amount": {
                    "type": "number",
                    "description": "Target dollar amount to save.",
                },
                "years": {
                    "type": "number",
                    "description": "Number of years to reach the goal.",
                },
                "expected_annual_return": {
                    "type": "number",
                    "description": "Expected annual return as a percentage (e.g. 7 for 7%).",
                },
                "current_savings": {
                    "type": "number",
                    "description": "Current amount already saved. Default 0.",
                },
            },
            "required": ["target_amount", "years", "expected_annual_return"],
        },
    },
}


_GOAL_SYSTEM_PROMPT = (
    "You are a savings goal parser. Extract goal parameters from the user's description.\n\n"
    "Rules:\n"
    "- Convert shorthand amounts: $1M → 1000000, $500k → 500000\n"
    "- Express expected_annual_return as a percentage NUMBER (e.g. 7 for 7%, not 0.07)\n"
    "- If the user doesn't mention current savings, default to 0\n"
    "- If the user doesn't mention expected return, use 7 as a reasonable default\n\n"
    "Example input: 'I want to save $1 million in 20 years with 7% return, I have $10k saved'\n"
    "Example output: {\"target_amount\": 1000000, \"years\": 20, "
    "\"expected_annual_return\": 7, \"current_savings\": 10000}"
)


def parse_goal_from_text(text: str) -> dict | str:
    """Parse a natural language goal description into goal parameters.

    If the input is already valid JSON, it is returned directly.

    Returns
    -------
    dict
        Parsed parameters like {"target_amount": 1000000, "years": 20, ...}.
    str
        Error message on failure.
    """
    # Fast path: already JSON
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=_get_model(),
            messages=[
                {"role": "system", "content": _GOAL_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            tools=[_GOAL_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_goal"}},
        )
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        if "target_amount" not in args or "years" not in args:
            return "Could not extract goal parameters from the description."
        return args
    except Exception as e:
        return f"Failed to parse goal description: {e}"


# ---------------------------------------------------------------------------
# Image parsing (Vision API)
# ---------------------------------------------------------------------------

def parse_portfolio_from_image(image_base64: str) -> dict | str:
    """Extract portfolio holdings from a brokerage screenshot.

    Uses GPT-4o Vision to read the image and extract ticker/dollar pairs.

    Parameters
    ----------
    image_base64 : str
        Base64-encoded image data (PNG or JPEG).

    Returns
    -------
    dict
        Parsed holdings like {"AAPL": 5000, "VTI": 8000} on success.
    str
        Error message on failure.
    """
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract stock holdings from this brokerage screenshot. "
                        "Return a JSON object mapping ticker symbols to dollar values. "
                        "Use standard uppercase ticker symbols."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                            },
                        },
                    ],
                },
            ],
            tools=[_PORTFOLIO_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_portfolio"}},
        )
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        # Convert array format [{ticker, amount}, ...] to dict {ticker: amount}
        raw_holdings = args.get("holdings", [])
        if isinstance(raw_holdings, list):
            holdings = {}
            for item in raw_holdings:
                if isinstance(item, dict) and "ticker" in item and "amount" in item:
                    ticker = str(item["ticker"]).upper().strip()
                    holdings[ticker] = float(item["amount"])
        elif isinstance(raw_holdings, dict):
            holdings = raw_holdings
        else:
            holdings = {}

        if not holdings:
            return "Could not extract holdings from the image."
        return holdings
    except Exception as e:
        return f"Failed to parse image: {e}"
