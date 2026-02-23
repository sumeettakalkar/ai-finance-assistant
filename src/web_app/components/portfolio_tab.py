"""Portfolio tab component with charts and multi-mode input."""

from __future__ import annotations

import json

import streamlit as st

from src.web_app.components._shared import render_messages, run_query, save_message_pair
from src.web_app.components.charts import portfolio_allocation_donut, portfolio_asset_mix_bar


def render_portfolio_tab() -> None:
    """Render the Portfolio tab with input mode selector."""
    st.subheader("Portfolio Analysis")
    st.markdown(
        '<div class="tab-instructions">'
        "Analyze your portfolio allocation, diversification, and risk. "
        "Choose an input method below."
        "</div>",
        unsafe_allow_html=True,
    )

    # Input mode selector
    input_mode = st.radio(
        "Input method",
        ["JSON", "Natural Language", "Upload Screenshot", "Voice"],
        horizontal=True,
        key="portfolio_input_mode",
    )

    render_messages("portfolio", show_charts=True)

    if input_mode == "JSON":
        _json_input()
    elif input_mode == "Natural Language":
        _nl_input()
    elif input_mode == "Upload Screenshot":
        _image_input()
    else:
        _voice_input()


def _json_input() -> None:
    """Existing JSON input flow."""
    st.write('Paste something like: `{"AAPL": 5000, "VTI": 8000, "BND": 2000}`')
    with st.form("portfolio_form", clear_on_submit=True):
        portfolio_input = st.text_area("Portfolio JSON", height=120)
        submitted = st.form_submit_button("Analyze Portfolio")

    if submitted and portfolio_input.strip():
        _submit_portfolio("portfolio", portfolio_input.strip())


def _nl_input() -> None:
    """Natural language input using OpenAI function calling."""
    st.write('Describe your portfolio, e.g. "I have $5000 in Apple, $8000 in VTI, and $2000 in bonds"')
    with st.form("portfolio_nl_form", clear_on_submit=True):
        nl_input = st.text_area("Describe your portfolio", height=120)
        submitted = st.form_submit_button("Analyze Portfolio")

    if submitted and nl_input.strip():
        with st.spinner("Parsing your portfolio description..."):
            try:
                from src.tools.parsing_tools import parse_portfolio_from_text
                result = parse_portfolio_from_text(nl_input.strip())
                if isinstance(result, dict):
                    st.info(f"Parsed holdings: {json.dumps(result, indent=2)}")
                    _submit_portfolio("portfolio", json.dumps(result))
                else:
                    st.error(f"Could not parse: {result}")
            except Exception as e:
                st.error(f"Parsing error: {e}")


def _image_input() -> None:
    """Image upload input using GPT-4o Vision."""
    st.write("Upload a screenshot of your brokerage account or portfolio statement.")
    uploaded = st.file_uploader(
        "Upload portfolio screenshot",
        type=["png", "jpg", "jpeg"],
        key="portfolio_image",
    )
    if uploaded is not None:
        import base64
        image_bytes = uploaded.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        st.image(image_bytes, caption="Uploaded screenshot", use_container_width=True)

        if st.button("Analyze Screenshot", type="primary"):
            with st.spinner("Extracting holdings from image..."):
                try:
                    from src.tools.parsing_tools import parse_portfolio_from_image
                    result = parse_portfolio_from_image(image_b64)
                    if isinstance(result, dict):
                        st.info(f"Extracted holdings: {json.dumps(result, indent=2)}")
                        _submit_portfolio("portfolio", json.dumps(result))
                    else:
                        st.error(f"Could not extract: {result}")
                except Exception as e:
                    st.error(f"Image parsing error: {e}")


def _voice_input() -> None:
    """Voice input using Whisper transcription + NL parsing."""
    st.write("Click the microphone and describe your portfolio holdings.")
    from src.web_app.components.audio_input import render_audio_input

    transcribed = render_audio_input(key="portfolio_audio")
    if transcribed:
        with st.spinner("Parsing your portfolio description..."):
            try:
                from src.tools.parsing_tools import parse_portfolio_from_text

                result = parse_portfolio_from_text(transcribed)
                if isinstance(result, dict):
                    st.info(f"Parsed holdings: {json.dumps(result, indent=2)}")
                    _submit_portfolio("portfolio", json.dumps(result))
                else:
                    st.error(f"Could not parse: {result}")
            except Exception as e:
                st.error(f"Parsing error: {e}")


def _submit_portfolio(tab_key: str, user_input: str) -> None:
    """Submit portfolio query and render charts."""
    messages = st.session_state.messages_by_tab[tab_key]
    messages.append({"role": "user", "content": user_input, "sources": [], "metadata": {}})

    with st.spinner("Analyzing your portfolio..."):
        assistant_msg = run_query(tab_key, user_input)
    messages.append(assistant_msg)

    save_message_pair(tab_key, user_input, assistant_msg)
    st.rerun()


def render_portfolio_charts(metadata: dict, chart_key: str = "portfolio_0") -> None:
    """Render portfolio-specific charts from metadata."""
    if not metadata or not metadata.get("allocations"):
        return

    col1, col2 = st.columns(2)
    with col1:
        fig = portfolio_allocation_donut(metadata)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key=f"donut_{chart_key}")
    with col2:
        fig = portfolio_asset_mix_bar(metadata)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key=f"asset_mix_{chart_key}")
