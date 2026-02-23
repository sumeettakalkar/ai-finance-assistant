# Enhancements Tracker

## Completed (v2.0)

### Phase 1: Tools Layer Extraction
- Extracted pure functions from agents into `src/tools/` (portfolio_tools, goal_tools, market_tools, rag_tools)
- All agents delegate to tools while preserving their `run()` interface
- Tools shared across agents, MCP server, and REST API

### Phase 2: MCP Server
- FastMCP server with 7 tools in `src/mcp/server.py`
- Works with Claude Desktop via `claude_desktop_config.json`
- Tools: analyze_portfolio, compute_portfolio_risk, plan_savings_goal, get_stock_quote, search_finance_knowledge, parse_portfolio_description, parse_goal_description

### Phase 3: Natural Language Parsing
- OpenAI function calling for NL-to-JSON parsing (`src/tools/parsing_tools.py`)
- Portfolio: "I have $5k in Apple" -> `{"AAPL": 5000}`
- Goals: "Save $1M in 20 years at 7%" -> `{"target_amount": 1000000, ...}`
- GPT-4o Vision API for brokerage screenshot parsing
- Array-based schema (not additionalProperties) for gpt-4o-mini compatibility

### Phase 4: AgentResponse Metadata
- Added `metadata: dict | None` field to `AgentResponse`
- Extended `GraphState` with `metadata` and `conversation_history`
- Portfolio/Goal agents populate metadata with structured chart data

### Phase 5: Interactive Charts
- Plotly chart builders in `src/web_app/components/charts.py`
- Portfolio: allocation donut + asset mix bar
- Market: price history line chart
- Goals: projected savings area chart
- Unique chart keys per message to prevent Streamlit duplicate element errors

### Phase 6: Conversation History
- SQLite persistence in `src/storage/` with WAL mode
- Sidebar shows past 20 conversations with [Tab] badges
- Click to load + auto-switch to correct tab (JS injection)
- Create, load, delete conversations

### Phase 7: UI Overhaul
- Split monolithic app.py into component architecture
- Components: sidebar, chat_tab, portfolio_tab, market_tab, goals_tab, charts, audio_input, file_upload, _shared
- Additive-only CSS theming (no color overrides, works with Streamlit's native theme)
- Input mode selectors per tab

### Phase 8: Audio Input
- Voice input via `audio-recorder-streamlit` + OpenAI Whisper
- Available on all 4 tabs (Chat, Portfolio, Market, Goals)
- MD5 hash dedup prevents infinite rerun loops
- Transcribed text feeds into NL parsing pipeline for Portfolio/Goals

### Phase 9: API Enhancements + Tests
- FastAPI updated to v2.0.0 with 12 endpoints
- New endpoints: POST /api/portfolio/natural, POST /api/portfolio/image, POST /api/goals/natural, GET /api/conversations, GET /api/conversations/{id}
- 76 tests across 8 test files (up from 13 in v1.0)

---

## Future Enhancements

### RAG Improvements
1. Support PDF and HTML documents in the knowledge base (pdfplumber already in requirements)
2. Web crawling script to build knowledge base from Investopedia, Bogleheads, Investor.gov
3. Strip ads/navigation from crawled pages, keep only definitions and explanations
4. Chunk-level source citations with per-document metadata (URL, title, parent page)
5. Web search fallback when FAISS has no relevant context
6. Hybrid search (keyword + semantic) for better retrieval

### Agents
7. LLM-based intelligent router (replace keyword classifier for ambiguous queries)
8. News summarization agent (market news via NewsAPI or similar)
9. Portfolio rebalancing suggestions based on target allocation
10. Risk tolerance questionnaire agent
11. Multi-turn conversation context for all agents (currently only FinanceQA uses history)

### UI/UX
12. PDF upload support for portfolio statements
13. Export conversation history as PDF/markdown
14. Real-time streaming responses (Streamlit's `st.write_stream`)
15. Responsive mobile layout improvements

### Infrastructure
16. User authentication and per-user data isolation
17. Rate limiting on API endpoints
18. Async agent execution for parallel tool calls
19. Monitoring and alerting (CloudWatch, Sentry)
20. CI/CD pipeline with GitHub Actions
