from src.agents.goal_agent import GoalAgent
from src.agents.market_agent import MarketAnalysisAgent
from src.agents.portfolio_agent import PortfolioAgent


def test_invalid_ticker_returns_low_confidence_error(monkeypatch) -> None:
    agent = MarketAnalysisAgent()
    monkeypatch.setattr(agent, "_get_quote_and_history", lambda ticker: None)

    response = agent.run("ZZZZZ")

    assert response.confidence == "low"
    assert "couldn't fetch data" in response.answer.lower()
    assert "disclaimer:" in response.answer.lower()


def test_portfolio_malformed_json_returns_helpful_error() -> None:
    response = PortfolioAgent().run("{bad json")

    assert response.confidence == "low"
    assert "please provide json" in response.answer.lower()
    assert "disclaimer:" in response.answer.lower()


def test_goal_malformed_json_returns_helpful_error() -> None:
    response = GoalAgent().run("{bad json")

    assert response.confidence == "low"
    assert "please provide json" in response.answer.lower()
    assert "disclaimer:" in response.answer.lower()
