from src.agents.portfolio_agent import PortfolioAgent


def main() -> None:
    agent = PortfolioAgent()
    portfolios = [
        '{"AAPL": 5000, "VTI": 8000, "BND": 2000}',
        '{"TSLA": 9000, "BND": 1000}',
        '{"AAPL": -100}',  # invalid on purpose
    ]

    for p in portfolios:
        print("=" * 80)
        print(f"Input JSON: {p}")
        response = agent.run(p)
        print(f"\nAgent: {response.agent_name}")
        print(f"Confidence: {response.confidence}")
        print(f"Answer:\n{response.answer}\n")


if __name__ == "__main__":
    main()
