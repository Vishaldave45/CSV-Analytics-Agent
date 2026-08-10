"""Page 7: Runtime & Observability Configuration Settings."""

from __future__ import annotations

import os

import streamlit as st

from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.session import clear_dataset_session, get_state, set_state
from streamlit_app.theme import apply_custom_theme

st.set_page_config(
    page_title=f"Settings — {APP_TITLE}",
    page_icon="⚙️",
    layout="wide",
)

apply_custom_theme()
render_sidebar()

render_header("Application & Runtime Settings", icon="⚙️")
st.write("---")

# LLM Model Settings
st.markdown("### 🤖 LLM Model Settings")
api_key_input = st.text_input(
    "Google Gemini API Key",
    value=get_state("google_api_key", os.getenv("GOOGLE_API_KEY", "")),
    type="password",
    help="Enter your Google AI Studio Gemini API key from https://aistudio.google.com/app/apikey",
)
avail_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-lite"]
curr_model = get_state("model_name", "gemini-2.0-flash")
curr_index = avail_models.index(curr_model) if curr_model in avail_models else 0

model_name = st.selectbox(
    "Gemini Model Name",
    options=avail_models,
    index=curr_index,
)
temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(get_state("temperature", 0.0)), step=0.1)
max_iterations = st.number_input("Max Loop Iterations", min_value=1, max_value=20, value=int(get_state("max_iterations", 6)), step=1)

if st.button("Save Model Settings"):
    if api_key_input:
        set_state("google_api_key", api_key_input)
        os.environ["GOOGLE_API_KEY"] = api_key_input
        env_file = ".env"
        lines = []
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                lines = [l for l in f.readlines() if not l.startswith("GOOGLE_API_KEY=")]
        lines.append(f"GOOGLE_API_KEY={api_key_input}\n")
        with open(env_file, "w") as f:
            f.writelines(lines)
    set_state("model_name", model_name)
    set_state("temperature", temperature)
    set_state("max_iterations", max_iterations)
    st.success("Model settings updated!")

st.write("---")

# LangSmith Observability Settings
st.markdown("### 📡 LangSmith Observability")
default_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY", "")
langchain_key_input = st.text_input(
    "LangSmith API Key",
    value=get_state("langchain_api_key", default_key),
    type="password",
    help="Enter your LangSmith API key (starts with lsv2_pt_...).",
)
default_tracing = (
    os.getenv("LANGSMITH_TRACING") == "true" or os.getenv("LANGCHAIN_TRACING_V2") == "true"
)
tracing_enabled = st.checkbox(
    "Enable LangSmith Tracing", value=get_state("tracing_enabled", default_tracing)
)

if st.button("Save Observability Settings"):
    set_state("tracing_enabled", tracing_enabled)
    os.environ["LANGSMITH_TRACING"] = "true" if tracing_enabled else "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if tracing_enabled else "false"
    os.environ["LANGSMITH_PROJECT"] = "csv-analytics-agent"
    os.environ["LANGCHAIN_PROJECT"] = "csv-analytics-agent"
    if langchain_key_input:
        set_state("langchain_api_key", langchain_key_input)
        os.environ["LANGSMITH_API_KEY"] = langchain_key_input
        os.environ["LANGCHAIN_API_KEY"] = langchain_key_input
        env_file = ".env"
        lines = []
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                lines = [
                    l
                    for l in f.readlines()
                    if not l.startswith("LANGCHAIN_API_KEY=")
                    and not l.startswith("LANGCHAIN_TRACING_V2=")
                    and not l.startswith("LANGSMITH_")
                ]
        lines.append(f"LANGSMITH_TRACING={'true' if tracing_enabled else 'false'}\n")
        lines.append("LANGSMITH_PROJECT=csv-analytics-agent\n")
        lines.append(f"LANGSMITH_API_KEY={langchain_key_input}\n")
        lines.append(f"LANGCHAIN_TRACING_V2={'true' if tracing_enabled else 'false'}\n")
        lines.append("LANGCHAIN_PROJECT=csv-analytics-agent\n")
        lines.append(f"LANGCHAIN_API_KEY={langchain_key_input}\n")
        with open(env_file, "w") as f:
            f.writelines(lines)

    from csv_analytics_agent.observability.tracing import configure_langsmith

    configure_langsmith()
    st.success(f"LangSmith Tracing set to: {tracing_enabled} (Project: csv-analytics-agent)")


st.write("---")

# Danger Zone / Session Management
st.markdown("### 🧹 Session & Memory Management")
col1, col2 = st.columns(2)

with col1:
    if st.button("Clear Conversation History", use_container_width=True):
        set_state("messages", [])
        st.success("Conversation history cleared!")

with col2:
    if st.button("Reset Entire Session", type="primary", use_container_width=True):
        clear_dataset_session()
        st.success("Entire session state reset!")
        st.rerun()

render_footer()
