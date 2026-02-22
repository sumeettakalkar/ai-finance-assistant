# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the app
streamlit run src/web_app/app.py

# Run tests
pytest -q
pytest --cov=src --cov-report=term-missing

# Run a single test file
pytest tests/test_unit_routing_and_math.py -v

# Run a single test
pytest tests/test_unit_routing_and_math.py::test_function_name -v
```

## Environment

Requires `OPENAI_API_KEY`. Optional: `OPENAI_FINANCE_MODEL` (defaults to `gpt-4o-mini`).

## Architecture

Multi-agent finance assistant using LangGraph for orchestration, FAISS for RAG, and Streamlit for UI.

```
Streamlit UI (4 tabs: Chat, Portfolio, Market, Goals)
    ↓
LangGraph StateGraph (Router node → agent nodes)
    ├── FinanceQAAgent   — RAG + OpenAI Responses API
    ├── MarketAgent      — yfinance with 30-min TTL cache
    ├── PortfolioAgent   — HHI-based diversification scoring
    └── GoalAgent        — Future value / annuity math
```

**Key files:**
- `src/workflow/graph.py` — LangGraph state graph, routing logic, conditional edges
- `src/agents/base.py` — `AgentResponse` dataclass and `Agent` Protocol (all agents implement `name: str` and `run(query: str) -> AgentResponse`)
- `src/web_app/app.py` — Streamlit UI; sets `payload["route"]` for tab-forced routing
- `src/rag/vector_store.py` — FAISS `IndexFlatL2` with OpenAI `text-embedding-3-small`
- `src/utils/cache.py` — TTL in-memory cache used by MarketAgent

## Routing Logic

Three-tier routing (priority order):
1. **Tab-forced**: Portfolio/Market/Goals tabs set `payload["route"]` directly in the UI
2. **Keyword classifier** (`classify_route()` in `graph.py`): keyword patterns match to `goal`, `market`, `portfolio`, or defaults to `finance_qa`
3. **Graph dispatch**: router node reads `state.route`, dispatches via conditional edges

## RAG Pipeline

Knowledge base is 6 `.txt` files in `documents/articles/`. Chunked at 500 chars with 50-char overlap, embedded with `text-embedding-3-small`, stored in FAISS. At query time, top-5 chunks are retrieved and passed as context to the LLM.

## Testing

Three test files with distinct responsibilities:
- `test_unit_routing_and_math.py` — portfolio metrics, goal math, routing classifier
- `test_contracts.py` — all agents return valid `AgentResponse` with disclaimers (uses mocks for OpenAI/yfinance)
- `test_error_handling.py` — invalid inputs, malformed JSON, graceful errors

Coverage target: 80%+ overall, 90%+ for core logic.
