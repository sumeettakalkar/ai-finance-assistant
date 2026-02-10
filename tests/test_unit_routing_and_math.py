import json

import pytest

from src.agents.goal_agent import GoalAgent
from src.agents.portfolio_agent import PortfolioAgent
from src.workflow.graph import classify_route


def test_portfolio_sanitize_holdings_filters_and_normalizes() -> None:
    agent = PortfolioAgent()
    raw = {
        "aapl": "1000",
        " AAPL ": 500,
        "VTI": 2000,
        "BND": -100,
        "BAD": "x",
        "": 200,
    }

    clean = agent._sanitize_holdings(raw)

    assert clean == {"AAPL": 1500.0, "VTI": 2000.0}


def test_portfolio_compute_metrics_known_portfolio() -> None:
    agent = PortfolioAgent()
    metrics = agent._compute_metrics({"AAPL": 5000, "VTI": 8000, "BND": 2000})

    assert metrics["total"] == pytest.approx(15000.0)
    assert metrics["risk"] == "high"
    assert metrics["diversification_score"] == pytest.approx(58.7)
    assert metrics["stock_pct"] == pytest.approx(86.6666, rel=1e-3)

    allocations = metrics["allocations"]
    assert allocations[0][0] == "VTI"
    assert allocations[0][1] == pytest.approx(8 / 15)


def test_goal_monthly_contribution_known_case() -> None:
    agent = GoalAgent()
    payload = json.dumps(
        {
            "target_amount": 1_000_000,
            "years": 20,
            "expected_annual_return": 7,
            "current_savings": 10_000,
        }
    )

    response = agent.run(payload)

    assert response.confidence == "high"
    assert "Required monthly contribution: $1,842.13" in response.answer


def test_classify_route_goal_json_goes_to_goal() -> None:
    message = json.dumps(
        {
            "target_amount": 1_000_000,
            "years": 20,
            "expected_annual_return": 7,
            "current_savings": 10_000,
        }
    )
    assert classify_route(message) == "goal"


def test_classify_route_ticker_goes_to_market() -> None:
    assert classify_route("AAPL") == "market"


def test_classify_route_normal_question_goes_to_finance_qa() -> None:
    assert classify_route("What is compound interest?") == "finance_qa"
