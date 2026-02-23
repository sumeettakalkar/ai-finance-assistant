"""Tests for NL and image parsing with mocked OpenAI calls."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.tools.parsing_tools import (
    parse_portfolio_from_text,
    parse_goal_from_text,
    parse_portfolio_from_image,
)


class TestParsePortfolioFromText:
    def test_json_passthrough(self):
        """Already-valid JSON should be returned directly."""
        result = parse_portfolio_from_text('{"AAPL": 5000, "VTI": 8000}')
        assert result == {"AAPL": 5000, "VTI": 8000}

    def test_natural_language(self):
        """NL input should call OpenAI and return parsed holdings."""
        mock_response = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.function.arguments = json.dumps({
            "holdings": [
                {"ticker": "AAPL", "amount": 5000},
                {"ticker": "VTI", "amount": 8000},
            ]
        })
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        with patch("src.tools.parsing_tools._get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_response
            result = parse_portfolio_from_text("I have $5000 in Apple and $8000 in VTI")

        assert isinstance(result, dict)
        assert result == {"AAPL": 5000, "VTI": 8000}

    def test_empty_holdings_returns_error(self):
        """If parsing returns no holdings, return an error string."""
        mock_response = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.function.arguments = json.dumps({"holdings": []})
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        with patch("src.tools.parsing_tools._get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_response
            result = parse_portfolio_from_text("I have some stocks")

        assert isinstance(result, str)
        assert "Could not extract" in result


class TestParseGoalFromText:
    def test_json_passthrough(self):
        payload = {"target_amount": 1000000, "years": 20, "expected_annual_return": 7}
        result = parse_goal_from_text(json.dumps(payload))
        assert result == payload

    def test_natural_language(self):
        mock_response = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.function.arguments = json.dumps({
            "target_amount": 1000000,
            "years": 20,
            "expected_annual_return": 7,
            "current_savings": 10000,
        })
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        with patch("src.tools.parsing_tools._get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_response
            result = parse_goal_from_text("Save $1M in 20 years at 7% return with $10k saved")

        assert isinstance(result, dict)
        assert result["target_amount"] == 1000000


class TestParsePortfolioFromImage:
    def test_successful_extraction(self):
        mock_response = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.function.arguments = json.dumps({
            "holdings": [
                {"ticker": "AAPL", "amount": 10000},
                {"ticker": "GOOGL", "amount": 5000},
            ]
        })
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        with patch("src.tools.parsing_tools._get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = mock_response
            result = parse_portfolio_from_image("fake_base64_data")

        assert isinstance(result, dict)
        assert result == {"AAPL": 10000, "GOOGL": 5000}

    def test_api_failure_returns_error(self):
        with patch("src.tools.parsing_tools._get_client") as mock_client:
            mock_client.return_value.chat.completions.create.side_effect = Exception("API error")
            result = parse_portfolio_from_image("fake_base64_data")

        assert isinstance(result, str)
        assert "Failed to parse" in result
