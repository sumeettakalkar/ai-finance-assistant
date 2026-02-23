"""Pure goal-planning functions extracted from GoalAgent.

All functions are stateless — they accept validated inputs and return
plain dicts or strings, making them easy to reuse and test.
"""

from __future__ import annotations

import math
from typing import Any, Dict

DISCLAIMER = (
    "Educational only — not financial advice. Returns a simplified estimate. "
    "This assumes constant return and doesn't include inflation/fees/taxes."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> float | None:
    """Best-effort numeric coercion for validation."""
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(converted):
        return None
    return converted


def _normalize_annual_return(raw_rate: float) -> float | None:
    """Support both decimal (0.07) and percent (7) formats."""
    if not math.isfinite(raw_rate):
        return None
    if 0 <= raw_rate < 1:
        return raw_rate
    if 1 <= raw_rate <= 100:
        return raw_rate / 100.0
    return None


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def validate_and_normalize_goal(payload: Dict[str, Any]) -> Dict[str, float] | str:
    """Validate user fields and normalize annual return to decimal form.

    Returns a normalized dict on success or an error message string.
    """
    required_fields = ["target_amount", "years", "expected_annual_return"]
    for field in required_fields:
        if field not in payload:
            return (
                f"Missing required field: '{field}'. "
                "Required fields are target_amount, years, and expected_annual_return."
            )

    target_amount = _to_float(payload.get("target_amount"))
    if target_amount is None or target_amount <= 0:
        return "target_amount must be a number greater than 0."

    years = _to_float(payload.get("years"))
    if years is None or years <= 0:
        return "years must be a number greater than 0."

    annual_input = _to_float(payload.get("expected_annual_return"))
    if annual_input is None:
        return "expected_annual_return must be numeric."

    annual_decimal = _normalize_annual_return(annual_input)
    if annual_decimal is None:
        return (
            "expected_annual_return must be between 0 and 100, "
            "provided as either decimal (0.07) or percent (7)."
        )

    current_savings_raw = payload.get("current_savings", 0)
    current_savings = _to_float(current_savings_raw)
    if current_savings is None or current_savings < 0:
        return "current_savings must be a number greater than or equal to 0."

    return {
        "target_amount": float(target_amount),
        "years": float(years),
        "annual_return_decimal": float(annual_decimal),
        "current_savings": float(current_savings),
    }


def compute_monthly_contribution(normalized: Dict[str, float]) -> Dict[str, float]:
    """Apply future-value math for end-of-month contributions.

    Uses the ordinary-annuity formula:
        PMT = FV_needed / (((1 + i)^n - 1) / i)
    where i = monthly rate, n = total months.
    """
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
        monthly_contribution = fv_needed / months
    else:
        growth_factor = (1.0 + monthly_rate) ** months
        annuity_factor = (growth_factor - 1.0) / monthly_rate
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


def format_goal_report(result: Dict[str, float]) -> str:
    """Render a structured markdown response for readability in chat UI."""
    target_amount = result["target_amount"]
    years = result["years"]
    months = int(result["months"])
    annual_return_pct = result["annual_return_decimal"] * 100.0
    current_savings = result["current_savings"]
    fv_of_current_savings = result["fv_of_current_savings"]
    monthly_contribution = result["monthly_contribution"]

    lines = []
    lines.append("### Goal Plan Summary")
    lines.append("")
    lines.append(f"**Required monthly contribution: ${monthly_contribution:,.2f}**")
    lines.append("")
    lines.append("**Inputs used**")
    lines.append(f"- Target amount (FV): **${target_amount:,.2f}**")
    lines.append(f"- Time horizon: **{years:g} years ({months} months)**")
    lines.append(f"- Expected annual return: **{annual_return_pct:.2f}%**")
    lines.append(f"- Current savings (PV): **${current_savings:,.2f}**")
    lines.append("")
    lines.append("**Projection details**")
    lines.append(
        f"- Future value of current savings at this return: **${fv_of_current_savings:,.2f}**"
    )
    lines.append("- Contribution timing assumed: **end of each month (ordinary annuity)**")
    lines.append("")
    lines.append(f"_Disclaimer: {DISCLAIMER}_")
    return "\n".join(lines)
