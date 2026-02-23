"""Goal planning agent for monthly contribution estimation.

The agent expects a JSON payload and computes the monthly amount needed
to reach a target future value using a standard future-value formula.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from src.agents.base import AgentResponse
from src.tools.goal_tools import (
    DISCLAIMER,
    validate_and_normalize_goal,
    compute_monthly_contribution,
    format_goal_report,
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

        # Structured metadata for charts (Phase 4+5)
        metadata = {
            "monthly_contribution": result["monthly_contribution"],
            "months": result["months"],
            "monthly_rate": result["monthly_rate"],
            "target_amount": result["target_amount"],
            "current_savings": result["current_savings"],
            "annual_return_decimal": result["annual_return_decimal"],
            "fv_of_current_savings": result["fv_of_current_savings"],
        }

        return AgentResponse(
            answer=answer,
            agent_name=self.name,
            confidence="high",
            sources=["self-computed"],
            metadata=metadata,
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

    # ------------------------------------------------------------------
    # Delegate to shared tools (preserving private API for existing tests)
    # ------------------------------------------------------------------
    def _validate_and_normalize(self, payload: Dict[str, Any]) -> Dict[str, float] | str:
        """Validate user fields and normalize annual return to decimal form."""
        return validate_and_normalize_goal(payload)

    def _compute_monthly_contribution(self, normalized: Dict[str, float]) -> Dict[str, float]:
        """Apply future-value math for end-of-month contributions."""
        return compute_monthly_contribution(normalized)

    def _format_answer(self, result: Dict[str, float]) -> str:
        """Render a structured markdown response for readability in chat UI."""
        return format_goal_report(result)

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
