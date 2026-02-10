import os
import streamlit as st
from openai import APIConnectionError, AuthenticationError, OpenAIError

from src.workflow.graph import get_graph

st.set_page_config(page_title="AI Finance Assistant", page_icon="💰", layout="wide")
st.title("AI Finance Assistant")
st.write("Ask me anything about finance, your portfolio, or market trends!")

TAB_KEYS = ("chat", "portfolio", "market", "goals")
TAB_FORCED_ROUTE = {
    "chat": None,
    "portfolio": "portfolio",
    "market": "market",
    "goals": "goal",
}


def init_state() -> None:
    if "messages_by_tab" not in st.session_state:
        st.session_state.messages_by_tab = {tab: [] for tab in TAB_KEYS}
        legacy_messages = st.session_state.get("messages", [])
        if legacy_messages:
            st.session_state.messages_by_tab["chat"] = legacy_messages
    # Keep compatibility with the old state key.
    st.session_state.messages = st.session_state.messages_by_tab["chat"]


def render_messages(tab_key: str) -> None:
    for msg in st.session_state.messages_by_tab[tab_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                st.caption("Sources: " + ", ".join(msg["sources"]))


def run_query(tab_key: str, user_input: str) -> dict:
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
        }
    except AuthenticationError as exc:
        if os.getenv("OPENAI_API_KEY"):
            msg = "OpenAI authentication failed. The API key is set but appears invalid."
        else:
            msg = "OpenAI API key is missing. Set `OPENAI_API_KEY` in your environment."
        return {"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": []}
    except APIConnectionError as exc:
        msg = "Network error connecting to OpenAI. Check your internet, DNS, or proxy settings."
        return {"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": []}
    except OpenAIError as exc:
        msg = "OpenAI request failed."
        return {"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": []}
    except Exception as exc:
        msg = "Unexpected error."
        return {"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": []}


def submit_message(tab_key: str, user_input: str) -> None:
    messages = st.session_state.messages_by_tab[tab_key]
    user_message = {"role": "user", "content": user_input, "sources": []}
    messages.append(user_message)

    assistant_message = run_query(tab_key, user_input)
    messages.append(assistant_message)


init_state()
tab_chat, tab_portfolio, tab_market, tab_goals = st.tabs(["Chat", "Portfolio", "Market", "Goals"])

with tab_chat:
    st.subheader("Chat")
    render_messages("chat")
    chat_input = st.chat_input("Ask a finance question", key="chat_input")
    if chat_input:
        submit_message("chat", chat_input)
        st.rerun()

with tab_portfolio:
    st.subheader("Portfolio (JSON input)")
    st.write('Paste something like: `{"AAPL": 5000, "VTI": 8000, "BND": 2000}`')
    render_messages("portfolio")
    with st.form("portfolio_form", clear_on_submit=True):
        portfolio_input = st.text_area("Portfolio JSON", height=120)
        submit_portfolio = st.form_submit_button("Analyze Portfolio")
    if submit_portfolio and portfolio_input.strip():
        submit_message("portfolio", portfolio_input.strip())
        st.rerun()

with tab_market:
    st.subheader("Market")
    st.write("Enter a ticker such as `AAPL` or `TSLA`.")
    render_messages("market")
    with st.form("market_form", clear_on_submit=True):
        market_input = st.text_input("Ticker or market question")
        submit_market = st.form_submit_button("Analyze Market")
    if submit_market and market_input.strip():
        submit_message("market", market_input.strip())
        st.rerun()

with tab_goals:
    st.subheader("Goals (JSON input)")
    st.write(
        'Paste something like: `{"target_amount": 1000000, "years": 20, '
        '"expected_annual_return": 7, "current_savings": 10000}`'
    )
    render_messages("goals")
    with st.form("goals_form", clear_on_submit=True):
        goals_input = st.text_area("Goal JSON", height=120)
        submit_goals = st.form_submit_button("Analyze Goals")
    if submit_goals and goals_input.strip():
        submit_message("goals", goals_input.strip())
        st.rerun()
