"""Portfolio analysis agent with simple heuristics."""

from __future__ import annotations

import json
from typing import Dict

from src.agents.base import AgentResponse
from src.tools.portfolio_tools import (
    DISCLAIMER,
    sanitize_holdings,
    compute_portfolio_metrics,
    format_portfolio_report,
)


class PortfolioAgent:
    """Analyze a basic ticker->USD portfolio without external data."""

    name: str = "portfolio"

    def run(self, user_message: str) -> AgentResponse:
        # Expect the incoming string to be a JSON object of ticker -> dollar value.
        try:
            raw = json.loads(user_message)
        except Exception:
            return self._error_response(
                "Please provide JSON like {\"AAPL\": 5000, \"VTI\": 8000}."
            )

        if not isinstance(raw, dict):
            return self._error_response(
                "Portfolio must be a JSON object mapping tickers to dollar values."
            )

        holdings = self._sanitize_holdings(raw)
        if not holdings:
            return self._error_response(
                "No usable holdings found. Provide positive dollar amounts per ticker."
            )

        metrics = self._compute_metrics(holdings)
        answer = self._format_answer(metrics)

        # Structured metadata for charts (Phase 4+5)
        metadata = {
            "allocations": {t: w for t, w, _ in metrics["allocations"]},
            "diversification_score": metrics["diversification_score"],
            "risk": metrics["risk"],
            "stock_pct": metrics["stock_pct"],
            "bond_pct": metrics["bond_pct"],
            "other_pct": metrics["other_pct"],
            "total": metrics["total"],
        }

        return AgentResponse(
            answer=answer,
            agent_name=self.name,
            confidence="high",
            sources=["self-computed"],
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Delegate to shared tools (preserving private API for existing tests)
    # ------------------------------------------------------------------
    def _sanitize_holdings(self, raw: Dict) -> Dict[str, float]:
        """Normalize tickers, coerce numeric values, drop invalid/negative entries."""
        return sanitize_holdings(raw)

    def _compute_metrics(self, holdings: Dict[str, float]) -> Dict[str, object]:
        """Derive totals, weights, diversification, and a simple risk label."""
        return compute_portfolio_metrics(holdings)

    def _format_answer(self, metrics: Dict[str, object]) -> str:
        """Render a structured markdown report for readability in chat UI."""
        return format_portfolio_report(metrics)

    def _error_response(self, message: str) -> AgentResponse:
        answer = message
        if "disclaimer:" not in answer.lower():
            answer = f"{answer}\n\nDisclaimer: {DISCLAIMER}"

        return AgentResponse(
            answer=answer,
            agent_name=self.name,
            confidence="low",
            sources=["self-computed"],
        )
