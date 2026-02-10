"""Goal planning agent for monthly contribution estimation.

The agent expects a JSON payload and computes the monthly amount needed
to reach a target future value using a standard future-value formula.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict

from src.agents.base import AgentResponse


DISCLAIMER = (
    """
    Educational only — not financial advice. Returns a simplified estimate.
    This assumes constant return and doesn’t include inflation/fees/taxes.
    """
)


class GoalAgent:
    """Estimate required monthly savings to hit a target goal."""

    name: str = "goal"

    def run(self, user_message: str) -> AgentResponse:
        payload = self._parse_payload(user_message)
        if payload is None:
            return self._error_response(
                "Please provide JSON like "
                '{"target_amount": 1000000, "years": 25, '
                '"expected_annual_return": 7, "current_savings": 50000}.'
            )

        normalized = self._validate_and_normalize(payload)
        if isinstance(normalized, str):
            return self._error_response(normalized)

        result = self._compute_monthly_contribution(normalized)
        answer = self._format_answer(result)

        return AgentResponse(
            answer=answer,
            agent_name=self.name,
            confidence="high",
            sources=["self-computed"],
        )

    def _parse_payload(self, user_message: str) -> Dict[str, Any] | None:
        """Parse strict JSON payload expected by this agent."""
        try:
            parsed = json.loads(user_message)
        except Exception:
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed

    def _validate_and_normalize(self, payload: Dict[str, Any]) -> Dict[str, float] | str:
        """Validate user fields and normalize annual return to decimal form."""
        required_fields = ["target_amount", "years", "expected_annual_return"]
        for field in required_fields:
            if field not in payload:
                return (
                    f"Missing required field: '{field}'. "
                    "Required fields are target_amount, years, and expected_annual_return."
                )

        target_amount = self._to_float(payload.get("target_amount"))
        if target_amount is None or target_amount <= 0:
            return "target_amount must be a number greater than 0."

        years = self._to_float(payload.get("years"))
        if years is None or years <= 0:
            return "years must be a number greater than 0."

        annual_input = self._to_float(payload.get("expected_annual_return"))
        if annual_input is None:
            return "expected_annual_return must be numeric."

        annual_decimal = self._normalize_annual_return(annual_input)
        if annual_decimal is None:
            return (
                "expected_annual_return must be between 0 and 100, "
                "provided as either decimal (0.07) or percent (7)."
            )

        current_savings_raw = payload.get("current_savings", 0)
        current_savings = self._to_float(current_savings_raw)
        if current_savings is None or current_savings < 0:
            return "current_savings must be a number greater than or equal to 0."

        return {
            "target_amount": float(target_amount),
            "years": float(years),
            "annual_return_decimal": float(annual_decimal),
            "current_savings": float(current_savings),
        }

    def _compute_monthly_contribution(self, normalized: Dict[str, float]) -> Dict[str, float]:
        """Apply future-value math for end-of-month contributions."""
        fv = normalized["target_amount"]
        years = normalized["years"]
        annual_return_decimal = normalized["annual_return_decimal"]
        pv = normalized["current_savings"]

        months = max(1, int(round(years * 12)))
        monthly_rate = annual_return_decimal / 12.0

        fv_of_current_savings = pv * ((1.0 + monthly_rate) ** months)
        fv_needed = fv - fv_of_current_savings

        if fv_needed <= 0:
            monthly_contribution = 0.0
        elif monthly_rate == 0:
            # No investment growth case: just split the remaining target evenly.
            monthly_contribution = fv_needed / months
        else:
            # (1 + i)^n where i=monthly_rate and n=months.
            # Example: at 0.5% monthly for 120 months -> (1.005)^120 ~= 1.819.
            # This is the compounding multiplier for $1 today. ( 1 growns to 1.819  in 120 months)
            growth_factor = (1.0 + monthly_rate) ** months
            annuity_factor = (growth_factor - 1.0) / monthly_rate
            
            # Rearranged ordinary annuity formula (end-of-month contributions):
            # FV_needed = PMT * (((1 + i)^n - 1) / i)
            # PMT = FV_needed * i / ((1 + i)^n - 1)
            monthly_contribution = fv_needed / annuity_factor

        return {
            "target_amount": fv,
            "years": years,
            "months": float(months),
            "annual_return_decimal": annual_return_decimal,
            "current_savings": pv,
            "monthly_rate": monthly_rate,
            "fv_of_current_savings": fv_of_current_savings,
            "fv_needed": fv_needed,
            "monthly_contribution": max(0.0, monthly_contribution),
        }

    def _format_answer(self, result: Dict[str, float]) -> str:
        """Render a compact, beginner-friendly response."""
        target_amount = result["target_amount"]
        years = result["years"]
        months = int(result["months"])
        annual_return_pct = result["annual_return_decimal"] * 100.0
        current_savings = result["current_savings"]
        fv_of_current_savings = result["fv_of_current_savings"]
        monthly_contribution = result["monthly_contribution"]

        lines = []
        lines.append(f"Required monthly contribution: ${monthly_contribution:,.2f}")
        lines.append(f"- Target amount (FV): ${target_amount:,.2f}")
        lines.append(f"- Time horizon: {years:g} years ({months} months)")
        lines.append(f"- Expected annual return: {annual_return_pct:.2f}%")
        lines.append(f"- Current savings (PV): ${current_savings:,.2f}")
        lines.append(
            f"- Projected future value of current savings: ${fv_of_current_savings:,.2f}"
        )
        lines.append("- Contribution timing: end of each month (ordinary annuity)")
        lines.append(f"Disclaimer: {DISCLAIMER}")
        return "\n".join(lines)

    def _normalize_annual_return(self, raw_rate: float) -> float | None:
        """Support both decimal and percent formats."""
        if not math.isfinite(raw_rate):
            return None
        if 0 <= raw_rate < 1:
            return raw_rate
        if 1 <= raw_rate <= 100:
            return raw_rate / 100.0
        return None

    def _to_float(self, value: Any) -> float | None:
        """Best-effort numeric coercion for validation."""
        try:
            converted = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(converted):
            return None
        return converted

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
