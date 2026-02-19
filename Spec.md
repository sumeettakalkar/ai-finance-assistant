 AI Finance Assistant – Technical Specification (Spec.md)

1. Overview

The AI Finance Assistant is a multi-agent financial education and analysis system built using:
	•	LLM (OpenAI GPT)
	•	LangGraph for orchestration
	•	FAISS for retrieval-augmented generation (RAG)
	•	yFinance for market data
	•	Streamlit for UI
	•	Pytest for testing

The system provides:
	1.	Finance education (RAG-based Q&A)
	2.	Market analysis (real-time price + trends)
	3.	Portfolio analysis (allocation, diversification, risk heuristics)
	4.	Goal planning (future value / annuity calculations)

All outputs are educational and include disclaimers.

⸻

2. Architecture Overview

Streamlit UI
      |
LangGraph Router (StateGraph)
      |
      +--> Finance Q&A Agent  --> FAISS Retriever --> OpenAI LLM
      +--> Market Agent       --> yFinance API + TTL Cache
      +--> Portfolio Agent    --> Heuristic Analysis (HHI, allocation)
      +--> Goal Agent         --> Financial Math (annuity formulas)



flowchart TB
  %% =========================
  %% AI Finance Assistant - Architecture
  %% =========================

  UI[Streamlit UI\nTabs: Chat | Portfolio | Market | Goals]
  UI -->|user_message / JSON| LG[LangGraph Router\n(StateGraph)]

  LG -->|route: finance_qa| QA[Finance Q&A Agent]
  LG -->|route: market| MA[Market Analysis Agent]
  LG -->|route: portfolio| PA[Portfolio Analysis Agent]
  LG -->|route: goal| GA[Goal Planning Agent]

  %% Finance Q&A (RAG)
  QA --> RET[RAG Retriever]
  RET --> FAISS[(FAISS Vector Index)]
  RET --> KB[(Knowledge Base\n50-100 articles + metadata)]
  RET -->|top-k chunks + citations| QA
  QA -->|context grounded prompt| LLM[OpenAI LLM]
  LLM --> QA

  %% Market
  MA --> CACHE[(TTL Cache\nin-memory)]
  MA --> YF[yFinance API]
  YF --> MA
  CACHE --> MA

  %% Portfolio + Goal (self-computed)
  PA --> MATH1[Heuristics\nHHI, allocation, risk bands]
  GA --> MATH2[Financial Math\nFV/Annuity PMT solver]

  %% Response
  QA --> RESP[AgentResponse\n(answer, agent_name, sources, confidence)]
  MA --> RESP
  PA --> RESP
  GA --> RESP

  RESP --> UI


  Sequence diagram :

  sequenceDiagram
  autonumber
  actor U as User
  participant UI as Streamlit UI
  participant LG as LangGraph Router
  participant QA as Finance Q&A Agent (RAG)
  participant RET as Retriever
  participant VS as FAISS Vector Store
  participant LLM as OpenAI LLM
  participant MA as Market Agent
  participant YF as yFinance
  participant PA as Portfolio Agent
  participant GA as Goal Agent

  U->>UI: Enter message (question / JSON)
  UI->>LG: invoke(state: user_message)

  LG->>LG: classify_route(user_message)

  alt Finance education query
    LG->>QA: run(user_message)
    QA->>RET: retrieve(query)
    RET->>VS: similarity_search(query_embedding, top_k)
    VS-->>RET: top_k chunks + metadata
    RET-->>QA: context + citations
    QA->>LLM: generate grounded answer(context)
    LLM-->>QA: answer text
    QA-->>LG: AgentResponse(answer, sources)
  else Market query (e.g., AAPL)
    LG->>MA: run(user_message)
    MA->>MA: cache lookup
    alt cache hit
      MA-->>LG: cached AgentResponse
    else cache miss
      MA->>YF: fetch quote + history
      YF-->>MA: price + recent closes
      MA->>MA: compute trend + cache store
      MA-->>LG: AgentResponse(answer, sources)
    end
  else Portfolio JSON
    LG->>PA: run(user_message JSON)
    PA->>PA: parse + validate + sanitize
    PA->>PA: compute allocation + HHI + risk
    PA-->>LG: AgentResponse(answer, self-computed)
  else Goal JSON
    LG->>GA: run(user_message JSON)
    GA->>GA: parse + validate
    GA->>GA: compute PMT (FV/annuity)
    GA-->>LG: AgentResponse(answer, self-computed)
  end

  LG-->>UI: final state (answer + sources)
  UI-->>U: Render response + citations + disclaimer
⸻

3. System Design

3.1 Multi-Agent Architecture

Each agent conforms to a shared interface:

class Agent(Protocol):
    name: str
    def run(self, user_message: str) -> AgentResponse

All agents return:

AgentResponse(
    answer: str,
    agent_name: str,
    confidence: str,
    sources: list[str] | None
)

This ensures:
	•	Consistent response structure
	•	Clean routing
	•	UI simplicity

⸻

4. Agent Specifications

⸻

4.1 Finance Q&A Agent (RAG)

Purpose
Provide grounded financial education using curated knowledge base.

Input
	•	Natural language question

Processing
	1.	Query → vector embedding
	2.	Retrieve top-k chunks from FAISS
	3.	Pass chunks as context to LLM
	4.	Generate response using grounded instructions

Output
	•	Answer
	•	Source citations (title + URL)
	•	Disclaimer

Failure Handling
	•	If no relevant context found → “I don’t have enough information.”
	•	Avoids hallucination by requiring context usage

⸻

4.2 Market Analysis Agent

Purpose
Provide real-time stock data insights.

Input
	•	Ticker symbol (e.g., AAPL)

Processing
	•	Fetch data from yFinance
	•	Compute:
	•	Current price
	•	1-day change %
	•	5-day trend
	•	Apply TTL cache (default 30 min)

Output
	•	Market summary
	•	Data freshness indicator (live/cached)
	•	Disclaimer

Error Handling
	•	Invalid ticker → graceful message
	•	API failures → friendly fallback

⸻

4.3 Portfolio Analysis Agent

Purpose
Analyze a portfolio allocation provided as JSON.

Input Example

{"AAPL": 5000, "VTI": 8000, "BND": 2000}

Processing
	1.	Validate & sanitize inputs
	2.	Compute:
	•	Total portfolio value
	•	Allocation %
	•	HHI (Herfindahl index)
	•	Diversification score (0–100)
	•	Risk band (low/medium/high)
	•	Asset mix (stocks/bonds/other)

Output
	•	Portfolio summary
	•	Allocation breakdown
	•	Diversification score
	•	Risk label + triggers
	•	Disclaimer

Risk Logic
	•	High concentration or stock-heavy → High
	•	Moderate concentration → Medium
	•	Broad allocation → Low

⸻

4.4 Goal Planning Agent

Purpose
Estimate monthly savings required to reach a target.

Input Example

{
  "target_amount": 1000000,
  "years": 20,
  "expected_annual_return": 7,
  "current_savings": 10000
}

Processing
	•	Convert return to decimal
	•	Apply future value formula:

FV = PV(1+r)^n + PMT * [((1+r)^n - 1)/r]

	•	Solve for PMT

Output
	•	Required monthly contribution
	•	Projection details
	•	Assumptions
	•	Disclaimer

Edge Cases
	•	Zero return
	•	Already funded goal
	•	Invalid inputs

⸻

5. LangGraph Orchestration

5.1 Routing Logic

Routing is determined by:
	•	Presence of goal-related keys → Goal Agent
	•	JSON object of tickers → Portfolio Agent
	•	Ticker symbol / price keywords → Market Agent
	•	Default → Finance Q&A

5.2 State Management

Graph state includes:
	•	user_message
	•	route
	•	answer
	•	sources

This design allows:
	•	Future multi-turn flows
	•	Context memory
	•	Advanced routing logic

⸻

6. Retrieval-Augmented Generation (RAG)

6.1 Knowledge Base

Sources include:
	•	Investopedia
	•	SEC Investor.gov
	•	Bogleheads Wiki

Documents are:
	•	Chunked (400–500 words)
	•	Embedded using OpenAI embedding model
	•	Stored in FAISS index

6.2 Retrieval Flow
	1.	User query embedded
	2.	Top-k similar chunks retrieved
	3.	Passed as context to LLM
	4.	LLM instructed to only answer using context

⸻

7. Error Handling & Reliability
	•	All agents return structured AgentResponse
	•	Graceful handling of:
	•	Invalid JSON
	•	Invalid ticker
	•	Missing required fields
	•	API errors
	•	TTL caching reduces API load
	•	“I don’t know” fallback for low RAG confidence

⸻

8. Testing Strategy

Testing includes:

Unit Tests
	•	Portfolio metrics calculations
	•	Goal contribution math
	•	Router classification
	•	RAG retrieval returns context

Edge Case Tests
	•	Invalid JSON
	•	Negative values
	•	Zero return
	•	Invalid ticker

Target Coverage:
	•	80%+ minimum
	•	90%+ for core logic

⸻

9. Security & Ethics
	•	No investment recommendations
	•	Educational-only disclaimers
	•	No personal financial advice
	•	No persistent storage of sensitive data

⸻

10. Deployment Plan
	•	Local development via Streamlit
	•	AWS EC2 deployment (optional)
	•	Environment variables for API keys
	•	Requirements.txt for reproducibility

⸻

11. Future Enhancements
	•	LLM-based intelligent router
	•	News summarization agent
	•	Portfolio rebalancing suggestions
	•	Risk tolerance questionnaire
	•	Persistent user memory
	•	MCP server integration

⸻

Disclaimer

This system is for educational purposes only and does not provide financial advice. All projections are simplified and based on static assumptions.

