"""Unit tests for the shared tools layer (src/tools/).

Tests portfolio metrics, goal math, market data extraction, and RAG retrieval.
These are pure-function tests — no mocks needed for portfolio and goal tools.
"""

import pytest

from src.tools.portfolio_tools import (
    sanitize_holdings,
    compute_portfolio_metrics,
    format_portfolio_report,
)
from src.tools.goal_tools import (
    validate_and_normalize_goal,
    compute_monthly_contribution,
    format_goal_report,
)
from src.tools.market_tools import extract_ticker, format_market_report


# ---------------------------------------------------------------------------
# Portfolio tools
# ---------------------------------------------------------------------------

class TestSanitizeHoldings:
    def test_normalizes_tickers_and_coerces_values(self):
        raw = {"aapl": "1000", " VTI ": 2000, "BND": -100, "BAD": "x", "": 200}
        result = sanitize_holdings(raw)
        assert result == {"AAPL": 1000.0, "VTI": 2000.0}

    def test_merges_duplicate_tickers(self):
        raw = {"aapl": 1000, "AAPL": 500}
        result = sanitize_holdings(raw)
        assert result == {"AAPL": 1500.0}

    def test_empty_input(self):
        assert sanitize_holdings({}) == {}

    def test_filters_inf_and_nan(self):
        raw = {"AAPL": float("inf"), "VTI": float("nan"), "BND": 1000}
        result = sanitize_holdings(raw)
        assert result == {"BND": 1000.0}


class TestComputePortfolioMetrics:
    def test_known_three_holding_portfolio(self):
        metrics = compute_portfolio_metrics({"AAPL": 5000, "VTI": 8000, "BND": 2000})
        assert metrics["total"] == pytest.approx(15000.0)
        assert metrics["risk"] == "high"  # 3 holdings + heavy stocks
        assert metrics["diversification_score"] == pytest.approx(58.7)
        assert metrics["stock_pct"] == pytest.approx(86.6666, rel=1e-3)

    def test_single_holding_is_high_risk(self):
        metrics = compute_portfolio_metrics({"AAPL": 10000})
        assert metrics["risk"] == "high"
        assert metrics["diversification_score"] == 0.0

    def test_well_diversified_portfolio(self):
        # 10 equal holdings
        holdings = {f"T{i}": 1000 for i in range(10)}
        metrics = compute_portfolio_metrics(holdings)
        assert metrics["diversification_score"] == pytest.approx(90.0)


class TestFormatPortfolioReport:
    def test_contains_key_sections(self):
        metrics = compute_portfolio_metrics({"AAPL": 5000, "VTI": 8000})
        report = format_portfolio_report(metrics)
        assert "Portfolio Summary" in report
        assert "Allocation breakdown" in report
        assert "Risk and diversification" in report
        assert "Asset mix" in report
        assert "Disclaimer" in report


# ---------------------------------------------------------------------------
# Goal tools
# ---------------------------------------------------------------------------

class TestValidateAndNormalizeGoal:
    def test_valid_payload_decimal_return(self):
        result = validate_and_normalize_goal({
            "target_amount": 1000000,
            "years": 20,
            "expected_annual_return": 0.07,
        })
        assert isinstance(result, dict)
        assert result["annual_return_decimal"] == pytest.approx(0.07)

    def test_valid_payload_percent_return(self):
        result = validate_and_normalize_goal({
            "target_amount": 1000000,
            "years": 20,
            "expected_annual_return": 7,
        })
        assert isinstance(result, dict)
        assert result["annual_return_decimal"] == pytest.approx(0.07)

    def test_missing_required_field(self):
        result = validate_and_normalize_goal({"target_amount": 1000000})
        assert isinstance(result, str)
        assert "Missing required field" in result

    def test_negative_target_amount(self):
        result = validate_and_normalize_goal({
            "target_amount": -100,
            "years": 20,
            "expected_annual_return": 7,
        })
        assert isinstance(result, str)
        assert "target_amount" in result


class TestComputeMonthlyContribution:
    def test_known_case(self):
        normalized = {
            "target_amount": 1_000_000,
            "years": 20.0,
            "annual_return_decimal": 0.07,
            "current_savings": 10_000,
        }
        result = compute_monthly_contribution(normalized)
        assert result["monthly_contribution"] == pytest.approx(1842.13, rel=1e-2)

    def test_zero_return(self):
        normalized = {
            "target_amount": 12000,
            "years": 1.0,
            "annual_return_decimal": 0.0,
            "current_savings": 0,
        }
        result = compute_monthly_contribution(normalized)
        assert result["monthly_contribution"] == pytest.approx(1000.0)

    def test_already_funded(self):
        normalized = {
            "target_amount": 10000,
            "years": 10.0,
            "annual_return_decimal": 0.07,
            "current_savings": 50000,
        }
        result = compute_monthly_contribution(normalized)
        assert result["monthly_contribution"] == pytest.approx(0.0)


class TestFormatGoalReport:
    def test_contains_key_sections(self):
        result = compute_monthly_contribution({
            "target_amount": 100000,
            "years": 10.0,
            "annual_return_decimal": 0.05,
            "current_savings": 0,
        })
        report = format_goal_report(result)
        assert "Goal Plan Summary" in report
        assert "Required monthly contribution" in report
        assert "Disclaimer" in report


# ---------------------------------------------------------------------------
# Market tools
# ---------------------------------------------------------------------------

class TestExtractTicker:
    def test_plain_ticker(self):
        assert extract_ticker("AAPL") == "AAPL"

    def test_dollar_prefix(self):
        assert extract_ticker("$TSLA") == "TSLA"

    def test_lowercase(self):
        assert extract_ticker("msft") == "MSFT"

    def test_sentence(self):
        assert extract_ticker("What's the price of AAPL?") == "WHAT"

    def test_empty_string(self):
        assert extract_ticker("") is None


class TestFormatMarketReport:
    def test_basic_format(self):
        data = {"price": 150.0, "day_change_pct": 1.5, "last_5_closes": [148, 149, 150]}
        report = format_market_report("AAPL", data)
        assert "AAPL" in report
        assert "$150" in report
        assert "1.5%" in report

    def test_cached_flag(self):
        data = {"price": 150.0, "day_change_pct": None, "last_5_closes": []}
        report = format_market_report("AAPL", data, cached=True)
        assert "(cached)" in report
