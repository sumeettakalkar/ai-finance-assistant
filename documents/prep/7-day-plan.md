🗓️ 7-Day Detailed Plan — AI Finance Assistant

🧠 Mental Model for the Week

Each day answers one big question:

Day	     Big Question
Day 1	What am I building?
Day 2	How does one agent work?
Day 3	How do agents retrieve knowledge?
Day 4	How do agents get real data?
Day 5	How do agents work together?
Day 6	How does the user see this?
Day 7	Is this demo-ready & defensible?


⸻

✅ DAY 1 — Architecture & Foundations (Today)

⏱ 1–1.5 hrs
🎯 Outcome: Clear scope + repo skeleton

What you do
	•	Finalize 4 agents
	•	Lock tech stack
	•	Create folder structure
	•	README draft
	•	High-level architecture understanding

Why this matters
	•	Prevents scope creep
	•	Makes future coding mechanical, not confusing

👉 You’re already doing this today — perfect.

⸻

✅ DAY 2 — First Agent: Finance Q&A (LLM + RAG-lite)

⏱ 1.5–2 hrs
🎯 Outcome: One agent that actually answers finance questions

Focus

Finance Q&A Agent ONLY

Tasks
	1.	Create finance_qa_agent.py
	2.	Add:
	•	Prompt template
	•	LLM call
	3.	Hardcode 2–3 finance explanations (no RAG yet)
	•	“What is an ETF?”
	•	“What is diversification?”
	4.	Test via simple Python script

Why Day 2 is critical
	•	You learn:
	•	How an agent is structured
	•	How LLM calls work
	•	Everything else builds on this

📌 Do NOT do FAISS yet
LLM first → RAG later (much easier this way)

⸻

✅ DAY 3 — RAG System (Knowledge Base)

⏱ 1.5–2 hrs
🎯 Outcome: LLM answers grounded in real documents

Focus

RAG pipeline for Finance Q&A Agent

Tasks
	1.	Collect 10–15 finance articles (not 50 yet)
	•	ETFs
	•	Stocks
	•	Bonds
	•	Risk
	2.	Chunk documents
	3.	Create embeddings
	4.	Store in FAISS
	5.	Retrieve top-k docs
	6.	Add source citation to responses

Why this day matters (grading-wise)
	•	RAG = 8% of total grade
	•	Shows production thinking
	•	Prevents hallucinations

📌 At end of Day 3, you should be able to say:

“What is diversification?”
→ Answer
→ “Source: Investopedia”

That alone impresses evaluators.

⸻

✅ DAY 4 — Market Analysis Agent (Real-Time Data)

⏱ 1.5–2 hrs
🎯 Outcome: Live market data working

Focus

Market Analysis Agent

Tasks
	1.	Create market_agent.py
	2.	Use yFinance
	3.	Fetch:
	•	Current price
	•	5-day trend
	4.	Handle:
	•	Invalid ticker
	•	API failure
	5.	Add simple caching (dict + TTL)

Why this matters
	•	Real-time data = 7% of grade
	•	Shows API integration + error handling

📌 Keep output simple:

“AAPL is trading at $X, up/down Y% over last 5 days.”

No fancy charts yet.

⸻

✅ DAY 5 — Portfolio + Goal Agents (Math Day)

⏱ 1.5–2 hrs
🎯 Outcome: Actual “finance intelligence”

⸻

🧮 Part A: Portfolio Analysis Agent

Input

{
  "AAPL": 5000,
  "VTI": 8000,
  "BND": 2000
}

Output
	•	Total value
	•	Allocation %
	•	Risk level (low / medium / high)

🏁 Part B: Goal Planning Agent

Input

“I want $1M in 20 years”

Output
	•	Monthly investment estimate
	•	Assumptions clearly stated

Why this day is powerful
	•	This is where users feel value
	•	Shows domain understanding (20% grade section)

📌 Keep math simple but explainable
Evaluators care more about clarity than precision.

⸻

✅ DAY 6 — LangGraph Orchestration + UI

⏱ 2 hrs
🎯 Outcome: Multi-agent system working end-to-end

⸻

🧠 Part A: LangGraph Workflow
	1.	Create workflow/graph.py
	2.	Classify user query:
	•	Education → Q&A Agent
	•	Portfolio → Portfolio Agent
	•	Market → Market Agent
	•	Goal → Goal Agent
	3.	Route accordingly

📌 This is 10% of grade alone

⸻

🖥️ Part B: Streamlit UI

Tabs:
	•	💬 Chat
	•	📊 Portfolio
	•	📈 Market
	•	🎯 Goals

Minimal but clean.

⸻

✅ DAY 7 — Testing, Docs & Demo Polish

⏱ 1.5–2 hrs
🎯 Outcome: Submission-ready

Tasks
	1.	Add basic unit tests
	•	Agent outputs
	•	Router logic
	2.	Finalize README:
	•	Architecture diagram (simple box diagram is fine)
	•	Setup instructions
	3.	Add disclaimers:
“For educational purposes only”
	4.	Record 5–7 min demo video

Demo script (important!)
	1.	Ask a finance question
	2.	Show RAG citation
	3.	Analyze portfolio
	4.	Fetch market data
	5.	Do a goal plan

🎯 This matches evaluation checklist perfectly.

⸻

🧩 Summary Table

Day	Focus	Deliverable
1	Architecture	Repo + clarity
2	First Agent	Q&A Agent
3	RAG	FAISS + citations
4	APIs	Market Agent
5	Intelligence	Portfolio + Goals
6	Orchestration	LangGraph + UI
7	Polish	Demo + docs