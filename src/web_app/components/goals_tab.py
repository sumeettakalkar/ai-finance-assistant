"""Goals tab component with savings projection chart."""

from __future__ import annotations

import json

import streamlit as st

from src.web_app.components._shared import render_messages, run_query, save_message_pair
from src.web_app.components.charts import goal_savings_projection


def render_goals_tab() -> None:
    """Render the Goals tab with input mode selector."""
    st.subheader("Goal Planning")
    st.markdown(
        '<div class="tab-instructions">'
        "Calculate how much you need to save each month to reach your financial goal. "
        "Choose an input method below."
        "</div>",
        unsafe_allow_html=True,
    )

    input_mode = st.radio(
        "Input method",
        ["JSON", "Natural Language", "Voice"],
        horizontal=True,
        key="goals_input_mode",
    )

    render_messages("goals", show_charts=True)

    if input_mode == "JSON":
        _json_input()
    elif input_mode == "Natural Language":
        _nl_input()
    else:
        _voice_input()


def _json_input() -> None:
    """Existing JSON input flow."""
    st.write(
        'Paste something like: `{"target_amount": 1000000, "years": 20, '
        '"expected_annual_return": 7, "current_savings": 10000}`'
    )
    with st.form("goals_form", clear_on_submit=True):
        goals_input = st.text_area("Goal JSON", height=120)
        submitted = st.form_submit_button("Calculate Goal")

    if submitted and goals_input.strip():
        _submit_goal(goals_input.strip())


def _nl_input() -> None:
    """Natural language input using OpenAI function calling."""
    st.write('Describe your goal, e.g. "I want to save $1 million in 20 years with 7% return, I have $10k saved"')
    with st.form("goals_nl_form", clear_on_submit=True):
        nl_input = st.text_area("Describe your savings goal", height=120)
        submitted = st.form_submit_button("Calculate Goal")

    if submitted and nl_input.strip():
        with st.spinner("Parsing your goal description..."):
            try:
                from src.tools.parsing_tools import parse_goal_from_text
                result = parse_goal_from_text(nl_input.strip())
                if isinstance(result, dict):
                    st.info(f"Parsed goal: {json.dumps(result, indent=2)}")
                    _submit_goal(json.dumps(result))
                else:
                    st.error(f"Could not parse: {result}")
            except Exception as e:
                st.error(f"Parsing error: {e}")


def _voice_input() -> None:
    """Voice input using Whisper transcription + NL parsing."""
    st.write("Click the microphone and describe your savings goal.")
    from src.web_app.components.audio_input import render_audio_input

    transcribed = render_audio_input(key="goals_audio")
    if transcribed:
        with st.spinner("Parsing your goal description..."):
            try:
                from src.tools.parsing_tools import parse_goal_from_text

                result = parse_goal_from_text(transcribed)
                if isinstance(result, dict):
                    st.info(f"Parsed goal: {json.dumps(result, indent=2)}")
                    _submit_goal(json.dumps(result))
                else:
                    st.error(f"Could not parse: {result}")
            except Exception as e:
                st.error(f"Parsing error: {e}")


def _submit_goal(user_input: str) -> None:
    """Submit goal query and render charts."""
    messages = st.session_state.messages_by_tab["goals"]
    messages.append({"role": "user", "content": user_input, "sources": [], "metadata": {}})

    with st.spinner("Calculating your savings plan..."):
        assistant_msg = run_query("goals", user_input)
    messages.append(assistant_msg)

    save_message_pair("goals", user_input, assistant_msg)
    st.rerun()


def render_goals_charts(metadata: dict, chart_key: str = "goals_0") -> None:
    """Render goal-specific charts from metadata."""
    if not metadata or not metadata.get("monthly_contribution"):
        return

    fig = goal_savings_projection(metadata)
    if fig:
        st.plotly_chart(fig, use_container_width=True, key=f"savings_{chart_key}")
