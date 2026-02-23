# MCP Server Enhancements Plan

## Current State

The MCP server (`src/mcp/server.py`) exposes 7 tools via FastMCP over stdio transport. All tools delegate to `src/tools/` pure functions — the same layer used by agents and the REST API.

### Existing Tools

| Tool | Type | Calls OpenAI? |
|------|------|---------------|
| `analyze_portfolio` | Computation | No |
| `compute_portfolio_risk` | Computation | No |
| `plan_savings_goal` | Computation | No |
| `get_stock_quote` | External API | No (yfinance) |
| `search_finance_knowledge` | RAG | Yes (embeddings) |
| `parse_portfolio_description` | NL parsing | Yes (function calling) |
| `parse_goal_description` | NL parsing | Yes (function calling) |

### Tests

6 tests in `tests/test_mcp_server.py` — test tool functions directly (not via MCP transport).

---

## Enhancement 1: MCP Resources (High Impact)

**Why:** Resources let Claude *read* data (conversations, knowledge base) without calling a tool. This demonstrates understanding of the full MCP surface area, not just tools.

### 1a. Conversation History Resource

```python
@mcp.resource("conversations://recent")
def list_recent_conversations() -> str:
    """Let Claude browse past conversation summaries."""
    from src.storage.conversation_db import ConversationDB
    db = ConversationDB()
    convs = db.list_conversations(limit=10)
    if not convs:
        return "No conversations yet."
    lines = []
    for c in convs:
        lines.append(f"- **[{c.tab.capitalize()}]** {c.title} (id: {c.id})")
    return "\n".join(lines)


@mcp.resource("conversations://{conv_id}")
def get_conversation_detail(conv_id: str) -> str:
    """Let Claude read a specific conversation's messages."""
    from src.storage.conversation_db import ConversationDB
    db = ConversationDB()
    conv = db.get_conversation(conv_id)
    if not conv:
        return f"Conversation {conv_id} not found."
    lines = [f"# {conv.title} ({conv.tab})\n"]
    for msg in conv.messages:
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"**{role}:** {msg.content}\n")
    return "\n".join(lines)
```

### 1b. Knowledge Base Resource

```python
@mcp.resource("knowledge://topics")
def list_knowledge_topics() -> str:
    """List available finance topics in the RAG knowledge base."""
    from pathlib import Path
    articles_dir = Path("documents/articles")
    files = sorted(articles_dir.glob("*.txt"))
    return "\n".join(f"- {f.stem}" for f in files)


@mcp.resource("knowledge://{topic}")
def get_knowledge_article(topic: str) -> str:
    """Read a specific knowledge base article."""
    from src.tools.rag_tools import retrieve_finance_context
    chunks = retrieve_finance_context(topic, top_k=3)
    if not chunks:
        return f"No content found for topic: {topic}"
    return "\n\n---\n\n".join(chunks)
```

### Interview talking point
> "MCP has three primitives: tools, resources, and prompts. Tools are for actions, resources are for reading data. I exposed conversation history as a resource so Claude can browse past sessions — it's read-only by design, which is safer than a tool that could modify data."

---

## Enhancement 2: MCP Prompts (High Impact)

**Why:** Prompts are pre-built templates that guide Claude through multi-step workflows. They show you understand MCP as a UX pattern, not just an API.

### 2a. Portfolio Review Prompt

```python
@mcp.prompt()
def portfolio_review(holdings_description: str) -> list[dict]:
    """Guide Claude through a comprehensive portfolio review."""
    return [
        {
            "role": "user",
            "content": f"""Please perform a comprehensive portfolio review:

1. First, call `parse_portfolio_description` with: {holdings_description}
2. Then, for each major holding (>10% allocation), call `get_stock_quote` to check current prices
3. Call `search_finance_knowledge` with "diversification" to get educational context
4. Summarize your findings:
   - Portfolio composition and risk level
   - Any concentration concerns
   - How current stock prices compare to allocation
   - Educational tips on diversification

Be thorough but concise."""
        }
    ]
```

### 2b. Financial Health Check Prompt

```python
@mcp.prompt()
def financial_health_check(
    holdings_description: str,
    goal_description: str,
) -> list[dict]:
    """Run both portfolio analysis and goal planning for a complete review."""
    return [
        {
            "role": "user",
            "content": f"""Please do a complete financial health check:

**Step 1 — Portfolio Analysis:**
Analyze this portfolio: {holdings_description}
Use `parse_portfolio_description` and note the risk level and diversification.

**Step 2 — Goal Planning:**
Calculate this savings goal: {goal_description}
Use `parse_goal_description` and note the required monthly contribution.

**Step 3 — Synthesis:**
- Is the portfolio risk level appropriate for the goal timeline?
- Are there diversification improvements that could help reach the goal?
- Provide 2-3 actionable recommendations.

Use `search_finance_knowledge` to back up your recommendations with educational context."""
        }
    ]
```

### Interview talking point
> "MCP Prompts are like stored procedures for AI workflows. Instead of hoping the user phrases their request perfectly, I package multi-tool orchestration into a template. Claude Desktop surfaces these as slash commands — one click triggers a structured analysis that chains 3-4 tool calls."

---

## Enhancement 3: SSE Transport — Remote MCP (High Impact)

**Why:** Currently stdio only (local subprocess). SSE transport makes the server accessible over HTTP for remote MCP clients.

### Implementation

```python
# src/mcp/server.py — update the entry point

if __name__ == "__main__":
    import sys
    if "--sse" in sys.argv:
        port = 8080
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        print(f"Starting MCP server with SSE transport on port {port}")
        mcp.run(transport="sse", port=port)
    else:
        mcp.run()  # default stdio for Claude Desktop local
```

### Usage

```bash
# Local (Claude Desktop)
python -m src.mcp.server

# Remote (any MCP client over HTTP)
python -m src.mcp.server --sse --port 8080
```

### Docker integration

Add to `docker-compose.yml`:
```yaml
  mcp:
    build: .
    command: python -m src.mcp.server --sse --port 8080
    ports:
      - "8080:8080"
    env_file: .env
    restart: unless-stopped
```

### Security considerations for remote
- Add API key auth middleware (check `Authorization` header)
- TLS termination via Nginx reverse proxy
- Rate limiting per client (especially for tools that call OpenAI)
- Tool-level permissions (allow compute tools, restrict NL parsing tools)

### Interview talking point
> "The stdio transport is for local use — Claude Desktop spawns my server as a subprocess. SSE transport exposes it over HTTP so any MCP client on the network can connect. In production I'd add auth tokens and TLS, plus rate limiting on tools that chain OpenAI calls to prevent unbounded LLM-to-LLM cost."

---

## Enhancement 4: Tool Composition (Medium Impact)

**Why:** Shows the server isn't just a flat list of tools — tools can compose into higher-level workflows.

```python
@mcp.tool()
def full_financial_review(
    holdings: dict[str, float],
    goal_description: str,
) -> str:
    """Combined portfolio analysis and goal planning in one call.

    Demonstrates tool composition — one MCP tool that orchestrates
    multiple underlying tool functions for a complete financial picture.

    Parameters
    ----------
    holdings : dict
        Mapping of ticker -> dollar value.
    goal_description : str
        Natural language goal (e.g., "Save $1M in 20 years at 7%").

    Returns
    -------
    str
        Combined markdown report.
    """
    portfolio_report = analyze_portfolio(holdings)
    goal_report = parse_goal_description(goal_description)

    return (
        "## Portfolio Analysis\n\n"
        f"{portfolio_report}\n\n"
        "---\n\n"
        "## Savings Goal\n\n"
        f"{goal_report}"
    )
```

### Interview talking point
> "This is tool composition — a single MCP tool that chains portfolio analysis and goal planning. The LLM doesn't need to coordinate multiple calls; it gets a complete financial picture in one invocation. It's the difference between giving someone a hammer and nails versus giving them a pre-built shelf."

---

## Enhancement 5: Structured Error Handling (Medium Impact)

**Why:** Better error context helps the LLM recover and retry intelligently.

```python
from mcp.server.fastmcp import FastMCP
from mcp.types import McpError, ErrorCode

@mcp.tool()
def get_stock_quote(ticker: str) -> str:
    clean_ticker = extract_ticker(ticker)
    if not clean_ticker:
        raise McpError(
            code=ErrorCode.InvalidParams,
            message=f"Could not parse ticker from: {ticker}",
        )

    data = get_market_data(clean_ticker)
    if data is None:
        raise McpError(
            code=ErrorCode.InternalError,
            message=f"Could not fetch data for {clean_ticker}. The ticker may be delisted or yfinance may be unavailable.",
        )

    return format_market_report(clean_ticker, data)
```

---

## Enhancement 6: Observability and Logging (Medium Impact)

**Why:** Track which tools are being called, how often, and what errors occur. Useful for demos and interviews.

```python
import logging
import time
from functools import wraps

logger = logging.getLogger("mcp.tools")

def log_tool_call(func):
    """Decorator to log MCP tool invocations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.info(f"Tool called: {func.__name__} | args: {kwargs}")
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.info(f"Tool completed: {func.__name__} | {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Tool failed: {func.__name__} | {elapsed:.2f}s | {e}")
            raise
    return wrapper
```

Apply to all tools:
```python
@mcp.tool()
@log_tool_call
def analyze_portfolio(holdings: dict[str, float]) -> str:
    ...
```

---

## Implementation Order

| # | Enhancement | Effort | Interview Impact | Dependencies |
|---|------------|--------|-----------------|--------------|
| 1 | MCP Resources | ~1 hour | High | None |
| 2 | MCP Prompts | ~1 hour | High | None |
| 3 | Tool Composition | ~30 min | Medium | None |
| 4 | Structured Errors | ~30 min | Medium | None |
| 5 | Observability | ~30 min | Medium | None |
| 6 | SSE Transport | ~2 hours | High | Security considerations |

Enhancements 1-5 can be done independently in any order. Enhancement 6 (SSE) is best done last since it involves Docker and security.

---

## New Tests to Add

| Test File | Tests |
|-----------|-------|
| `test_mcp_server.py` | Add tests for: resources return valid strings, prompts return valid message lists, composed tool returns combined report, structured errors raise McpError |

---

## Interview Comparison: MCP vs REST vs Function Calling

| Aspect | REST API | OpenAI Function Calling | MCP |
|--------|----------|------------------------|-----|
| Discovery | Client reads docs/OpenAPI spec | Tools defined per LLM request | Auto-discovery at connection time |
| Client | Any HTTP client | OpenAI SDK only | Any MCP client (Claude, Cursor, etc.) |
| Statefulness | Stateless (per request) | Stateless (per request) | Persistent connection, session context |
| Data access | Endpoints only | Tools only | Tools + Resources + Prompts |
| Transport | HTTP | HTTPS (OpenAI API) | stdio (local) or SSE (remote) |
| Your app | 12 endpoints at `/api/*` | Used internally for NL parsing | 7 tools via FastMCP |

> **Key insight to share:** "My app uses all three. REST for programmatic integrations, OpenAI function calling internally for NL-to-JSON parsing, and MCP for AI-native access. Same `src/tools/` functions power all three — different access patterns, single source of truth."
