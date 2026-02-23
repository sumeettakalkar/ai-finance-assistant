"""Sidebar component: branding and conversation history."""

from __future__ import annotations

import streamlit as st

from src.storage.conversation_db import ConversationDB


def _get_db() -> ConversationDB:
    if "conversation_db" not in st.session_state:
        st.session_state.conversation_db = ConversationDB()
    return st.session_state.conversation_db


def render_sidebar() -> None:
    """Render the sidebar with branding and conversation history."""
    with st.sidebar:
        # Branding
        st.markdown(
            '<div class="sidebar-brand">AI Finance Assistant</div>',
            unsafe_allow_html=True,
        )

        # New conversation button
        if st.button("New conversation", use_container_width=True, type="primary"):
            _start_new_conversation()

        st.divider()

        # Conversation history
        st.caption("Recent conversations")
        db = _get_db()
        conversations = db.list_conversations(limit=20)

        if not conversations:
            st.caption("No conversations yet.")
            return

        current_conv_id = st.session_state.get("current_conversation_id")

        for conv in conversations:
            col1, col2 = st.columns([5, 1])
            with col1:
                label = conv.title[:35]
                if len(conv.title) > 35:
                    label += "..."
                # Show which tab the conversation belongs to
                tab_badge = conv.tab.capitalize()
                display_label = f"[{tab_badge}] {label}"
                is_active = conv.id == current_conv_id
                btn_type = "primary" if is_active else "secondary"
                if st.button(
                    display_label,
                    key=f"conv_{conv.id}",
                    use_container_width=True,
                    type=btn_type,
                ):
                    _load_conversation(conv.id)
            with col2:
                if st.button(
                    "X",
                    key=f"del_{conv.id}",
                    help="Delete conversation",
                ):
                    db.delete_conversation(conv.id)
                    if current_conv_id == conv.id:
                        _start_new_conversation()
                    st.rerun()


def _start_new_conversation() -> None:
    """Reset session state for a new conversation."""
    st.session_state.pop("current_conversation_id", None)
    # Clear per-tab messages
    for tab in ("chat", "portfolio", "market", "goals"):
        st.session_state.messages_by_tab[tab] = []
    st.rerun()


def _load_conversation(conv_id: str) -> None:
    """Load a conversation from the DB into session state."""
    db = _get_db()
    conv = db.get_conversation(conv_id)
    if not conv:
        return

    st.session_state.current_conversation_id = conv_id

    # Clear all tabs, then populate the conversation's tab
    for tab in ("chat", "portfolio", "market", "goals"):
        st.session_state.messages_by_tab[tab] = []

    tab_key = conv.tab
    for msg in conv.messages:
        st.session_state.messages_by_tab[tab_key].append({
            "role": msg.role,
            "content": msg.content,
            "sources": msg.sources or [],
            "metadata": msg.metadata or {},
        })

    # Store which tab to activate so app.py can switch to it
    st.session_state.active_tab = tab_key

    st.rerun()
