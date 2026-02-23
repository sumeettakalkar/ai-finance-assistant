"""Tests for MCP server tool functions.

These test the tool functions directly (not via MCP transport),
ensuring the business logic is correct.
"""

import pytest

from src.mcp.server import (
    analyze_portfolio,
    compute_portfolio_risk,
    plan_savings_goal,
    get_stock_quote,
)


class TestAnalyzePortfolio:
    def test_valid_portfolio(self):
        result = analyze_portfolio({"AAPL": 5000, "VTI": 8000, "BND": 2000})
        assert "Portfolio Summary" in result
        assert "AAPL" in result
        assert "Disclaimer" in result

    def test_empty_portfolio(self):
        result = analyze_portfolio({})
        assert "No usable holdings" in result


class TestComputePortfolioRisk:
    def test_returns_dict(self):
        result = compute_portfolio_risk({"AAPL": 5000, "VTI": 8000})
        assert isinstance(result, dict)
        assert "risk" in result
        assert "diversification_score" in result

    def test_empty_returns_error(self):
        result = compute_portfolio_risk({})
        assert "error" in result


class TestPlanSavingsGoal:
    def test_known_case(self):
        result = plan_savings_goal(
            target_amount=1_000_000,
            years=20,
            expected_annual_return=7,
            current_savings=10_000,
        )
        assert "Goal Plan Summary" in result
        assert "$1,842.13" in result

    def test_invalid_return(self):
        result = plan_savings_goal(
            target_amount=1_000_000,
            years=20,
            expected_annual_return=200,
        )
        assert "Error" in result


class TestGetStockQuote:
    def test_invalid_ticker(self, monkeypatch):
        """Mock the data fetch to return None."""
        from src.tools import market_tools
        monkeypatch.setattr(market_tools, "get_quote_and_history", lambda *a, **kw: None)
        result = get_stock_quote("ZZZZZ")
        assert "Could not fetch" in result

    def test_valid_ticker(self, monkeypatch):
        """Mock the data fetch to return sample data."""
        from src.tools import market_tools
        monkeypatch.setattr(
            market_tools,
            "get_quote_and_history",
            lambda *a, **kw: {
                "price": 150.0,
                "day_change_pct": 1.5,
                "last_5_closes": [148, 149, 150],
            },
        )
        # Also need to mock get_market_data since it's what get_stock_quote calls
        monkeypatch.setattr(
            market_tools,
            "get_market_data",
            lambda *a, **kw: {
                "price": 150.0,
                "day_change_pct": 1.5,
                "last_5_closes": [148, 149, 150],
            },
        )
        result = get_stock_quote("AAPL")
        assert "AAPL" in result
        assert "$150" in result
