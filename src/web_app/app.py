import os
import streamlit as st
from openai import APIConnectionError, AuthenticationError, OpenAIError

from src.workflow.graph import get_graph

st.set_page_config(page_title="AI Finance Assistant", page_icon="💰", layout="wide")
st.title("AI Finance Assistant")
st.write("Ask me anything about finance, your portfolio, or market trends!")
if "messages" not in st.session_state:
    #meesage will be a dict  :{role, content, sources}
    st.session_state.messages = []

tab_chat, tab_portfolio, tab_market, tab_goals = st.tabs(["Chat", "Portfolio", "Market", "Goals"])

with tab_chat:
    st.subheader("Chat")
    
    #show message history
    for m in st.session_state.messages :
        with st.chat_message(m["role"]) :
            st.markdown(m["content"])
            if m.get("sources"):
                st.caption("Sources: " + ", ".join(m["sources"]))
                
user_input = st.chat_input("Ask a finance question or paste a JSON for portfoli/ goal")

if(user_input) :
    st.session_state.messages.append({"role" : "user", "content": user_input, "sources" : []})

    try:
        result  = get_graph().invoke({"userMsg" : user_input})
        assistant_response = result.get("answer", "")
        sources = result.get("sources" , [])
        st.session_state.messages.append({"role" : "assistant" , "content" :assistant_response, "sources":sources })
    except AuthenticationError as exc:
        # Missing or invalid API key
        if os.getenv("OPENAI_API_KEY"):
            msg = "OpenAI authentication failed. The API key is set but appears invalid."
        else:
            msg = "OpenAI API key is missing. Set `OPENAI_API_KEY` in your environment."
        st.session_state.messages.append({"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": []})
    except APIConnectionError as exc:
        msg = "Network error connecting to OpenAI. Check your internet, DNS, or proxy settings."
        st.session_state.messages.append({"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": []})
    except OpenAIError as exc:
        msg = "OpenAI request failed."
        st.session_state.messages.append({"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": []})
    except Exception as exc:
        msg = "Unexpected error."
        st.session_state.messages.append({"role": "assistant", "content": f"{msg}\n\nDetails: {exc}", "sources": []})

    st.rerun()
    

with tab_portfolio:
    st.subheader("Portfolio (JSON input)")
    st.write('Paste something like : `{"AAPL": 5000, "VTI": 8000, "BND": 2000}`') 
    
with tab_market:
    st.subheader("Market")
    st.write('Enter in chat : `AAPL` or `TSLA`')
    
with tab_goals:
    st.subheader("Goals (JSON input)")
    st.write('Paste something like: `{"target_amount": 1000000, "years": 20, "expected_annual_return": 7, "current_savings": 10000}`')
    
            
