# AI Finance Assistant

Multi-agent AI system for financial education using LangGraph and RAG.

## Agents
- Finance Q&A Agent
- Portfolio Analysis Agent
- Market Analysis Agent
- Goal Planning Agent

## Tech Stack
- OpenAI GPT
- LangGraph
- FAISS
- yFinance
- Streamlit




This project implements 4 core agents with clean orchestration rather than 6 shallow agents.

Optimize for finishing, not flexing.

[ UI Layer ]
   |
[ Workflow / Router (LangGraph) ]
   |
[ Specialized Agents ]
   |
[ RAG / APIs / Calculations ]

Agents should  NOT talk to each other directly --- They all go through LangGraph router.
------------------------------------------------------------------

1. Finance Q&A Agent
	•	Input: “What is an ETF?”
	•	Uses: RAG only
	•	Output: Explanation + sources

2. Portfolio Agent
	•	Input: User portfolio (tickers + amounts)
	•	Uses: Python calculations
	•	Output: Allocation %, diversification, risk level

3. Market Agent
	•	Input: “How is AAPL doing?”
	•	Uses: yFinance
	•	Output: Price, trend, summary

4. Goal Agent
	•	Input: “I want to retire in 20 years”
	•	Uses: Simple math (compound growth)
	•	Output: Monthly investment estimate

