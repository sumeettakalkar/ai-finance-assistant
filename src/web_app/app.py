"""AI Finance Assistant — Streamlit entry point.

Slim orchestrator that wires together sidebar, tabs, and theming.
All heavy logic lives in ``src/web_app/components/``.
"""

import streamlit as st

from src.web_app.styles.theme import generate_css
from src.web_app.components.sidebar import render_sidebar
from src.web_app.components.chat_tab import render_chat_tab
from src.web_app.components.portfolio_tab import render_portfolio_tab
from src.web_app.components.market_tab import render_market_tab
from src.web_app.components.goals_tab import render_goals_tab

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Finance Assistant",
    page_icon="$",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# State initialization
# ---------------------------------------------------------------------------
TAB_KEYS = ("chat", "portfolio", "market", "goals")

if "messages_by_tab" not in st.session_state:
    st.session_state.messages_by_tab = {tab: [] for tab in TAB_KEYS}

# ---------------------------------------------------------------------------
# Minimal CSS (additive only — works with Streamlit's native light theme)
# ---------------------------------------------------------------------------
st.markdown(f"<style>{generate_css()}</style>", unsafe_allow_html=True)

try:
    from pathlib import Path
    static_css = (Path(__file__).parent / "styles" / "custom.css").read_text()
    st.markdown(f"<style>{static_css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
render_sidebar()

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.title("AI Finance Assistant")
st.caption("Multi-agent finance assistant powered by LangGraph and OpenAI")

TAB_LABELS = ["Chat", "Portfolio", "Market", "Goals"]
TAB_KEY_TO_INDEX = {"chat": 0, "portfolio": 1, "market": 2, "goals": 3}

tab_chat, tab_portfolio, tab_market, tab_goals = st.tabs(TAB_LABELS)

with tab_chat:
    render_chat_tab()

with tab_portfolio:
    render_portfolio_tab()

with tab_market:
    render_market_tab()

with tab_goals:
    render_goals_tab()

# ---------------------------------------------------------------------------
# Auto-switch to the correct tab when loading a conversation from sidebar
# ---------------------------------------------------------------------------
active_tab = st.session_state.pop("active_tab", None)
if active_tab and active_tab in TAB_KEY_TO_INDEX:
    tab_index = TAB_KEY_TO_INDEX[active_tab]
    js = f"""
    <script>
        var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
        if (tabs.length > {tab_index}) {{
            tabs[{tab_index}].click();
        }}
    </script>
    """
    st.components.v1.html(js, height=0)
