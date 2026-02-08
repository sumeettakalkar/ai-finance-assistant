"""Quick manual harness for GoalAgent."""

from src.agents.goal_agent import GoalAgent


def main() -> None:
    agent = GoalAgent()
    samples = [
        # 1) Valid standard case
        '{"target_amount": 1000000, "years": 25, "expected_annual_return": 7, "current_savings": 50000}',
        # 2) Valid with decimal return + no current_savings
        '{"target_amount": 300000, "years": 10, "expected_annual_return": 0.05}',
        # 3) Zero-return branch
        '{"target_amount": 100000, "years": 10, "expected_annual_return": 0, "current_savings": 20000}',
        # 4) Current savings already enough
        '{"target_amount": 100000, "years": 10, "expected_annual_return": 6, "current_savings": 120000}',
        # 5) Invalid input (negative years)
        '{"target_amount": 500000, "years": -2, "expected_annual_return": 7, "current_savings": 5000}',
    ]

    for sample in samples:
        print("=" * 80)
        print(f"Input: {sample}")
        response = agent.run(sample)
        print(f"\nAgent: {response.agent_name}")
        print(f"Confidence: {response.confidence}")
        print(f"Sources: {response.sources}")
        print(f"Answer:\n{response.answer}\n")


if __name__ == "__main__":
    main()
