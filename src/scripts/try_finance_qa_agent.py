from src.agents.finance_qa_agent import FinanceQAAgent

def main():
    agent = FinanceQAAgent()
    questions = [
        "What is an ETF?",
        "Explain diversification like I’m 12.",
        "What is crypto staking?"
    ]
    for q in questions:
        print("=" * 80)
        print(f"Question: {q}")
        response = agent.run(q)
        print(f"Agent Name: {response.agent_name}\n")
        print(f"Confidence: {response.confidence}\n")
        print(f"Answer: {response.answer}\n")
        
if __name__ == "__main__":
    main()  