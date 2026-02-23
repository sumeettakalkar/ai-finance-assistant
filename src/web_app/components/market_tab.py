"""Market tab component with price history chart."""

from __future__ import annotations

import streamlit as st

from src.web_app.components._shared import render_messages, run_query, save_message_pair
from src.web_app.components.audio_input import render_audio_input
from src.web_app.components.charts import market_price_history


def render_market_tab() -> None:
    """Render the Market tab."""
    st.subheader("Market Data")
    st.markdown(
        '<div class="tab-instructions">'
        "Enter a ticker like <code>AAPL</code> or <code>TSLA</code> to get current price "
        "and recent history. You can also use the microphone button."
        "</div>",
        unsafe_allow_html=True,
    )

    render_messages("market", show_charts=True)

    # Audio input
    transcribed = render_audio_input(key="market_audio")
    if transcribed:
        _submit_market(transcribed)

    with st.form("market_form", clear_on_submit=True):
        market_input = st.text_input("Ticker or market question")
        submitted = st.form_submit_button("Get Market Data")

    if submitted and market_input.strip():
        _submit_market(market_input.strip())


def _submit_market(user_input: str) -> None:
    """Submit a market query."""
    messages = st.session_state.messages_by_tab["market"]
    messages.append({"role": "user", "content": user_input, "sources": [], "metadata": {}})

    with st.spinner("Fetching market data..."):
        assistant_msg = run_query("market", user_input)
    messages.append(assistant_msg)

    save_message_pair("market", user_input, assistant_msg)
    st.rerun()


def render_market_charts(metadata: dict, chart_key: str = "market_0") -> None:
    """Render market-specific charts from metadata."""
    if not metadata:
        return

    closes = metadata.get("last_5_closes", [])
    ticker = metadata.get("ticker", "")

    if closes:
        fig = market_price_history(ticker, closes)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key=f"price_{chart_key}")
