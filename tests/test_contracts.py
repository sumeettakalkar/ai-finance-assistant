import json
from types import SimpleNamespace

from src.agents.base import AgentResponse
from src.agents.finance_qa_agent import FinanceQAAgent
from src.agents.goal_agent import GoalAgent
from src.agents.market_agent import MarketAnalysisAgent
from src.agents.portfolio_agent import PortfolioAgent


def _assert_agent_response_contract(response: AgentResponse) -> None:
    assert isinstance(response, AgentResponse)
    assert "disclaimer:" in response.answer.lower()


def test_portfolio_agent_contract() -> None:
    response = PortfolioAgent().run(json.dumps({"AAPL": 5000, "VTI": 8000, "BND": 2000}))
    _assert_agent_response_contract(response)


def test_goal_agent_contract() -> None:
    response = GoalAgent().run(
        json.dumps(
            {
                "target_amount": 1_000_000,
                "years": 20,
                "expected_annual_return": 7,
                "current_savings": 10_000,
            }
        )
    )
    _assert_agent_response_contract(response)


def test_market_agent_contract(monkeypatch) -> None:
    agent = MarketAnalysisAgent()
    monkeypatch.setattr(
        agent,
        "_get_quote_and_history",
        lambda ticker: {
            "price": 123.45,
            "day_change_pct": 1.23,
            "last_5_closes": [120.0, 121.0, 122.0, 123.0, 123.45],
        },
    )

    response = agent.run("AAPL")
    _assert_agent_response_contract(response)


def test_finance_qa_agent_contract_without_network() -> None:
    class FakeRetriever:
        def retrieve(self, query: str, top_k: int = 5) -> list[str]:
            return ["ETF means exchange-traded fund."]

    class FakeClient:
        def __init__(self) -> None:
            self.responses = self

        def create(self, **kwargs):
            return SimpleNamespace(output_text="An ETF is a basket of securities.")

    # Bypass __init__ to avoid OpenAI and embedding calls in tests.
    agent = FinanceQAAgent.__new__(FinanceQAAgent)
    agent.client = FakeClient()
    agent.retriever = FakeRetriever()
    agent.model = "gpt-4o-mini"

    response = agent.run("What is an ETF?")
    _assert_agent_response_contract(response)
