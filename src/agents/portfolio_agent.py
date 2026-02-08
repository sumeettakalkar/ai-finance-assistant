"""Portfolio analysis agent with simple heuristics."""

from __future__ import annotations

import json
import math
from typing import Dict, List, Tuple

from src.agents.base import AgentResponse


DISCLAIMER = (
    "Educational only — not financial advice. May not reflect real-world constraints."
)

# Simple asset buckets (for demo)
STOCK_KEYWORDS = {"VTI", "VOO", "VUG", "QQQ", "VXUS", "VEA", "VWO", "SPY", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "JPM", "JNJ", "UNH", "HD", "PG", "DIS", "MA", "BAC", "V", "ADBE", "CMCSA", "NFLX"}
BOND_KEYWORDS = {"BND", "BNDX", "AGG", "TLT", "IEF", "SHY", "MUB", "LQD", "HYG", "JNK"}


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

        return AgentResponse(
            answer=answer,
            agent_name=self.name,
            confidence="high",
            sources=["self-computed"],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _sanitize_holdings(self, raw: Dict) -> Dict[str, float]:
        """Normalize tickers, coerce numeric values, drop invalid/negative entries."""
        clean: Dict[str, float] = {}
        for k, v in raw.items():
            try:
                value = float(v)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(value) or value <= 0:
                continue
            ticker = str(k).upper().strip()
            if not ticker:
                continue
            clean[ticker] = clean.get(ticker, 0.0) + value
        return clean

    def _compute_metrics(self, holdings: Dict[str, float]) -> Dict[str, object]:
        """Derive totals, weights, diversification, and a simple risk label.

        Steps:
        1) Sum all dollar amounts to get portfolio total.
        2) Convert each holding to a weight (percentage of total).
        3) Calculate a concentration score using HHI (Herfindahl index):
           - HHI = sum(weight^2); ranges from 1.0 (one holding) down to ~0.
           - We flip it to a diversification score: (1 - HHI) scaled to 0–100.
        4) Assign risk bands using easy-to-read rules:
           - Fewer than 3 names OR one name >60% OR HHI>0.35 → high risk.
           - Else if top name >40% OR HHI>0.25 OR fewer than 5 names → medium.
           - Otherwise → low.
        5) Build a sorted list of allocations for display.
        """
        total = sum(holdings.values())

        # Weight is the share of each position relative to the total portfolio.
        weights: Dict[str, float] = {k: v / total for k, v in holdings.items()}

        # Herfindahl–Hirschman Index (HHI): higher = more concentrated.
        hhi = sum(w ** 2 for w in weights.values())

        # Convert concentration into an easy-to-read 0–100 diversification score.
        diversification_score = max(0.0, min((1 - hhi) * 100, 100.0))
        diversification_score = round(diversification_score, 1)

        n = len(weights)
        top_weight = max(weights.values()) if weights else 0.0

        triggers = []
        # Heuristic risk bands based on concentration and breadth.
        if n < 3 or top_weight > 0.60 or hhi > 0.35:
            risk = "high"
            if n < 3:
                triggers.append(f"only {n} holdings")
            if top_weight > 0.60:
                triggers.append(f"top position {top_weight*100:.0f}%")
            if hhi > 0.35:
                triggers.append(f"HHI {hhi:.2f}")
        elif top_weight > 0.40 or hhi > 0.25 or n < 5:
            risk = "medium"
            if n < 5:
                triggers.append(f"{n} holdings")
            if top_weight > 0.40:
                triggers.append(f"top position {top_weight*100:.0f}%")
            if hhi > 0.25:
                triggers.append(f"HHI {hhi:.2f}")
        else:
            risk = "low"
            triggers.append("no single outsized position")

        # Prepare allocations sorted by largest weight first for readability.
        allocations: List[Tuple[str, float, float]] = sorted(
            [(ticker, weights[ticker], holdings[ticker]) for ticker in weights],
            key=lambda x: x[1],
            reverse=True,
        )

        # Approximate asset mix using common ticker patterns.
        stock_value = bond_value = other_value = 0.0
        for t, v in holdings.items():
            t_up = t.upper().strip()
            if t_up in STOCK_KEYWORDS:
                stock_value += v
            elif t_up in BOND_KEYWORDS:
                bond_value += v
            else:
                other_value += v

        stock_pct = stock_value / total * 100 if total else 0.0
        bond_pct = bond_value / total * 100 if total else 0.0
        other_pct = other_value / total * 100 if total else 0.0

        # Asset-mix risk overlay (stocks-heavy ⇒ higher risk).
        if stock_pct >= 80:
            asset_risk = "high"
            triggers.append(f"stocks {stock_pct:.0f}%")
        elif stock_pct >= 50:
            asset_risk = "medium"
            triggers.append(f"stocks {stock_pct:.0f}%")
        else:
            asset_risk = "low"

        severity = {"low": 0, "medium": 1, "high": 2}
        if severity[asset_risk] > severity[risk]:
            risk = asset_risk

        return {
            "total": total,
            "allocations": allocations,
            "diversification_score": diversification_score,
            "risk": risk,
            "triggers": triggers,
            "stock_pct": stock_pct,
            "bond_pct": bond_pct,
            "other_pct": other_pct,
        }

    def _format_answer(self, metrics: Dict[str, object]) -> str:
        """Render a short human-friendly report."""
        total = metrics["total"]
        allocations: List[Tuple[str, float, float]] = metrics["allocations"]  # type: ignore
        diversification_score = metrics["diversification_score"]
        risk = metrics["risk"]
        triggers = metrics["triggers"]
        stock_pct = metrics["stock_pct"]
        bond_pct = metrics["bond_pct"]
        other_pct = metrics["other_pct"]

        # Explain the main drivers behind the risk label in plain language.
        reasons = []
        if risk == "high":
            reasons.append("high concentration or very stock-heavy mix")
        elif risk == "medium":
            reasons.append("moderate concentration or stock tilt")
        else:
            reasons.append("broad mix with no single outsized position")

        lines = []
        lines.append(f"Total value: ${total:,.2f}")
        lines.append("Allocations:")
        for ticker, weight, value in allocations:
            lines.append(f" - {ticker}: {weight*100:.1f}% (${value:,.2f})")
        lines.append(f"Diversification score: {diversification_score} / 100")
        lines.append(
            f"Risk: {risk} (reason: {', '.join(reasons)}; triggers: {', '.join(triggers)})"
        )
        lines.append(
            f"- Asset mix (approx): Stocks {stock_pct:.0f}%, Bonds {bond_pct:.0f}%, Other {other_pct:.0f}%"
        )
        lines.append(f"Disclaimer: {DISCLAIMER}")
        return "\n".join(lines)

    def _error_response(self, message: str) -> AgentResponse:
        return AgentResponse(
            answer=message,
            agent_name=self.name,
            confidence="low",
            sources=["self-computed"],
        )
