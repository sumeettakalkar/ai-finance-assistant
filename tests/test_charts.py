"""Tests for chart builder functions.

Verifies that chart functions return valid plotly.graph_objects.Figure
instances (or None for missing data).
"""

import pytest
import plotly.graph_objects as go

from src.web_app.components.charts import (
    portfolio_allocation_donut,
    portfolio_asset_mix_bar,
    market_price_history,
    goal_savings_projection,
)


class TestPortfolioAllocationDonut:
    def test_valid_data_returns_figure(self):
        metadata = {"allocations": {"AAPL": 0.4, "VTI": 0.35, "BND": 0.25}}
        fig = portfolio_allocation_donut(metadata)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == "pie"

    def test_empty_allocations_returns_none(self):
        assert portfolio_allocation_donut({"allocations": {}}) is None
        assert portfolio_allocation_donut({}) is None


class TestPortfolioAssetMixBar:
    def test_valid_data_returns_figure(self):
        metadata = {"stock_pct": 60, "bond_pct": 30, "other_pct": 10}
        fig = portfolio_asset_mix_bar(metadata)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == "bar"

    def test_missing_data_returns_none(self):
        assert portfolio_asset_mix_bar({}) is None


class TestMarketPriceHistory:
    def test_valid_data_returns_figure(self):
        fig = market_price_history("AAPL", [148, 149, 150, 151, 152])
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert fig.data[0].type == "scatter"

    def test_with_dates(self):
        dates = ["Mon", "Tue", "Wed"]
        fig = market_price_history("AAPL", [148, 149, 150], dates=dates)
        assert isinstance(fig, go.Figure)

    def test_empty_closes_returns_none(self):
        assert market_price_history("AAPL", []) is None


class TestGoalSavingsProjection:
    def test_valid_data_returns_figure(self):
        metadata = {
            "monthly_contribution": 1000,
            "months": 120.0,
            "monthly_rate": 0.005833,
            "current_savings": 10000,
            "target_amount": 200000,
        }
        fig = goal_savings_projection(metadata)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # projection area + target line

    def test_missing_data_returns_none(self):
        assert goal_savings_projection({}) is None
        assert goal_savings_projection({"monthly_contribution": None}) is None

    def test_zero_contribution_still_produces_figure(self):
        metadata = {
            "monthly_contribution": 0,
            "months": 120.0,
            "monthly_rate": 0.005833,
            "current_savings": 50000,
            "target_amount": 10000,
        }
        fig = goal_savings_projection(metadata)
        # 0 is not None, so the check passes and a figure is generated
        # (shows current savings growing via compound interest alone)
        assert isinstance(fig, go.Figure)
