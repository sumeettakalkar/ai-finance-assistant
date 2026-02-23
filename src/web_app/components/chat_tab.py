"""Chat tab component."""

from __future__ import annotations

import streamlit as st

from src.web_app.components._shared import render_messages, run_query, save_message_pair
from src.web_app.components.audio_input import render_audio_input


def render_chat_tab() -> None:
    """Render the Chat tab."""
    st.subheader("Chat")
    st.markdown(
        '<div class="tab-instructions">'
        "Ask any finance question — I'll route it to the best specialist agent. "
        "You can also use the microphone button to speak your question."
        "</div>",
        unsafe_allow_html=True,
    )

    render_messages("chat")

    # Audio input
    transcribed = render_audio_input(key="chat_audio")
    if transcribed:
        _submit_chat(transcribed)

    chat_input = st.chat_input("Ask a finance question", key="chat_input")
    if chat_input:
        _submit_chat(chat_input)


def _submit_chat(user_input: str) -> None:
    """Submit a chat query."""
    messages = st.session_state.messages_by_tab["chat"]
    messages.append({"role": "user", "content": user_input, "sources": [], "metadata": {}})

    with st.spinner("Thinking..."):
        assistant_msg = run_query("chat", user_input)
    messages.append(assistant_msg)

    save_message_pair("chat", user_input, assistant_msg)
    st.rerun()
