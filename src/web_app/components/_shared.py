"""Shared helpers used by all tab components."""

from __future__ import annotations

import os

import streamlit as st
from openai import APIConnectionError, AuthenticationError, OpenAIError

from src.workflow.graph import get_graph

TAB_FORCED_ROUTE = {
    "chat": None,
    "portfolio": "portfolio",
    "market": "market",
    "goals": "goal",
}


def render_messages(tab_key: str, show_charts: bool = False) -> None:
    """Display chat history for a tab, optionally with charts."""
    for idx, msg in enumerate(st.session_state.messages_by_tab[tab_key]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                st.caption("Sources: " + ", ".join(msg["sources"]))

            # Render charts for assistant messages with metadata
            if show_charts and msg["role"] == "assistant" and msg.get("metadata"):
                _render_charts_for_tab(tab_key, msg["metadata"], msg_index=idx)


def run_query(tab_key: str, user_input: str) -> dict:
    """Invoke the graph and return an assistant message dict."""
    payload = {"userMsg": user_input}
    forced_route = TAB_FORCED_ROUTE[tab_key]
    if forced_route:
        payload["route"] = forced_route

    try:
        result = get_graph().invoke(payload)
        return {
            "role": "assistant",
            "content": result.get("answer", ""),
            "sources": result.get("sources", []),
            "metadata": result.get("metadata", {}),
        }
    except AuthenticationError as exc:
        if os.getenv("OPENAI_API_KEY"):
            msg = "OpenAI authentication failed. The API key is set but appears invalid."
        else:
            msg = "OpenAI API key is missing. Set `OPENAI_API_KEY` in your environment."
        return {"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": [], "metadata": {}}
    except APIConnectionError as exc:
        msg = "Network error connecting to OpenAI. Check your internet, DNS, or proxy settings."
        return {"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": [], "metadata": {}}
    except OpenAIError as exc:
        msg = "OpenAI request failed."
        return {"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": [], "metadata": {}}
    except Exception as exc:
        msg = "Unexpected error."
        return {"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": [], "metadata": {}}


def save_message_pair(tab_key: str, user_input: str, assistant_msg: dict) -> None:
    """Persist a user+assistant message pair to the conversation DB."""
    try:
        from src.storage.conversation_db import ConversationDB

        if "conversation_db" not in st.session_state:
            st.session_state.conversation_db = ConversationDB()
        db = st.session_state.conversation_db

        # Get or create conversation
        conv_id = st.session_state.get("current_conversation_id")
        if not conv_id:
            conv = db.create_conversation(tab=tab_key)
            conv_id = conv.id
            st.session_state.current_conversation_id = conv_id

        db.add_message(conv_id, "user", user_input)
        db.add_message(
            conv_id,
            "assistant",
            assistant_msg.get("content", ""),
            sources=assistant_msg.get("sources"),
            metadata=assistant_msg.get("metadata"),
        )
    except Exception:
        # Don't let DB errors break the main UX
        pass


def _render_charts_for_tab(tab_key: str, metadata: dict, msg_index: int = 0) -> None:
    """Dispatch to the appropriate chart renderer based on tab."""
    if tab_key == "portfolio":
        from src.web_app.components.portfolio_tab import render_portfolio_charts
        render_portfolio_charts(metadata, chart_key=f"{tab_key}_{msg_index}")
    elif tab_key == "market":
        from src.web_app.components.market_tab import render_market_charts
        render_market_charts(metadata, chart_key=f"{tab_key}_{msg_index}")
    elif tab_key == "goals":
        from src.web_app.components.goals_tab import render_goals_charts
        render_goals_charts(metadata, chart_key=f"{tab_key}_{msg_index}")
