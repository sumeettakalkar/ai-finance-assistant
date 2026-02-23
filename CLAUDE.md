# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the Streamlit UI
streamlit run src/web_app/app.py

# Run the REST API
uvicorn src.api.main:app --port 8000

# Run the MCP server
python -m src.mcp.server

# Run tests
pytest -q
pytest --cov=src --cov-report=term-missing

# Run a single test file
pytest tests/test_unit_routing_and_math.py -v

# Run a single test
pytest tests/test_unit_routing_and_math.py::test_function_name -v

# Docker (local)
docker-compose up --build
```

## Environment

Requires `OPENAI_API_KEY`. Optional: `OPENAI_FINANCE_MODEL` (defaults to `gpt-4o-mini`).

## Architecture

Multi-agent finance assistant with layered architecture: Tools -> Agents -> Workflow -> Presentation. Uses LangGraph for orchestration, FAISS for RAG, Streamlit for UI, FastMCP for tool exposure, FastAPI for REST, and SQLite for conversation history.

```
User Input (text / JSON / voice / image)
    ↓
Parsing Layer — src/tools/parsing_tools.py (OpenAI function calling / Vision API)
    ↓  structured JSON
Tools Layer — src/tools/ (pure functions shared by agents, MCP, API)
    ↓
Agent Layer — src/agents/ (4 agents implementing Agent Protocol)
    ↓
LangGraph StateGraph — src/workflow/graph.py (router node → conditional edges)
    ↓
AgentResponse (answer + metadata for charts)
    ↓
Presentation — Streamlit UI + Plotly charts + SQLite persistence
```

**Key layers:**
- `src/tools/` — Pure reusable functions (shared by agents, MCP server, API)
- `src/agents/` — Agent protocol + 4 specialist agents (delegate to tools)
- `src/workflow/graph.py` — LangGraph state graph, routing, conditional edges
- `src/mcp/server.py` — FastMCP server exposing 7 finance tools
- `src/storage/` — SQLite conversation persistence (WAL mode)
- `src/web_app/` — Streamlit UI with component architecture
- `src/web_app/components/charts.py` — Plotly chart builders
- `src/api/main.py` — FastAPI REST endpoints (12 endpoints)

**Key files:**
- `src/agents/base.py` — `AgentResponse` dataclass (with `metadata` field) and `Agent` Protocol
- `src/tools/portfolio_tools.py` — `sanitize_holdings()`, `compute_portfolio_metrics()`, `format_portfolio_report()`
- `src/tools/goal_tools.py` — `validate_and_normalize_goal()`, `compute_monthly_contribution()`, `format_goal_report()`
- `src/tools/market_tools.py` — `extract_ticker()`, `get_market_data()`, `format_market_report()`
- `src/tools/parsing_tools.py` — NL-to-JSON via OpenAI function calling, image-to-JSON via Vision API
- `src/tools/rag_tools.py` — `retrieve_finance_context()` wrapping FAISS retriever
- `src/tools/audio_tools.py` — `transcribe_audio()` via OpenAI Whisper API
- `src/storage/conversation_db.py` — SQLite CRUD for conversations and messages
- `src/web_app/components/audio_input.py` — Mic button with MD5 dedup to prevent rerun loops

## Routing Logic

Three-tier routing (priority order):
1. **Tab-forced**: Portfolio/Market/Goals tabs set `payload["route"]` directly in the UI
2. **Keyword classifier** (`classify_route()` in `graph.py`): keyword patterns match to `goal`, `market`, `portfolio`, or defaults to `finance_qa`
3. **Graph dispatch**: router node reads `state.route`, dispatches via conditional edges

## RAG Pipeline

Knowledge base is 6 `.txt` files in `documents/articles/`. Chunked at 500 chars with 50-char overlap, embedded with `text-embedding-3-small`, stored in FAISS. At query time, top-5 chunks are retrieved and passed as context to the LLM.

## MCP Server

7 tools exposed via FastMCP: `analyze_portfolio`, `compute_portfolio_risk`, `plan_savings_goal`, `get_stock_quote`, `search_finance_knowledge`, `parse_portfolio_description`, `parse_goal_description`. Configure in Claude Desktop's `claude_desktop_config.json`.

## Multi-Modal Input

- **JSON**: Direct structured input (all tabs)
- **Natural Language**: OpenAI function calling with array-based schemas (Portfolio, Goals)
- **Voice**: `audio-recorder-streamlit` -> Whisper API -> text (all tabs)
- **Image**: GPT-4o Vision API for brokerage screenshots (Portfolio)
- Audio dedup uses MD5 hash in session state to prevent infinite Streamlit rerun loops

## Testing

Eight test files (76 tests total):
- `test_unit_routing_and_math.py` — portfolio metrics, goal math, routing classifier
- `test_contracts.py` — all agents return valid `AgentResponse` with disclaimers
- `test_error_handling.py` — invalid inputs, malformed JSON, graceful errors
- `test_tools.py` — unit tests for all `src/tools/` functions
- `test_mcp_server.py` — MCP tool functions called directly
- `test_parsing.py` — NL and image parsing with mocked OpenAI calls
- `test_conversation_db.py` — SQLite CRUD with in-memory DB
- `test_charts.py` — chart functions return valid Plotly figures

Coverage target: 80%+ overall, 90%+ for core logic.
