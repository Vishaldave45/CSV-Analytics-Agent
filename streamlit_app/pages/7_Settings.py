"""Page 7: Data Studio Settings & Developer Workspace."""

from __future__ import annotations

import os

import streamlit as st

from csv_analytics_agent.llm.gemini import AVAILABLE_MODELS, DEFAULT_MODEL_NAME
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

render_header("Settings", icon="⚙️")
st.write("---")

tab_general, tab_observability, tab_dev = st.tabs(
    ["⚙️ General & Model", "📡 Observability (LangSmith)", "🛠️ Developer & Privacy"]
)

with tab_general:
    st.markdown("### Model Settings")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=get_state("google_api_key", os.getenv("GOOGLE_API_KEY", "")),
        type="password",
        help="Enter your Google AI Studio Gemini API key",
    )
    avail_models = list(AVAILABLE_MODELS)
    curr_model = get_state("model_name", DEFAULT_MODEL_NAME)
    curr_index = avail_models.index(curr_model) if curr_model in avail_models else 0

    model_name = st.selectbox(
        "Gemini Model",
        options=avail_models,
        index=curr_index,
    )
    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=float(get_state("temperature", 0.0)),
        step=0.1,
    )
    max_iterations = st.number_input(
        "Max Iterations",
        min_value=1,
        max_value=20,
        value=int(get_state("max_iterations", 6)),
        step=1,
    )

    if st.button("Save Model Settings"):
        if api_key_input:
            set_state("google_api_key", api_key_input)
            os.environ["GOOGLE_API_KEY"] = api_key_input
            env_file = ".env"
            lines = []
            if os.path.exists(env_file):
                with open(env_file) as f:
                    lines = [
                        line for line in f.readlines() if not line.startswith("GOOGLE_API_KEY=")
                    ]
            lines.append(f"GOOGLE_API_KEY={api_key_input}\n")
            with open(env_file, "w") as f:
                f.writelines(lines)
        set_state("model_name", model_name)
        set_state("temperature", temperature)
        set_state("max_iterations", max_iterations)
        st.success("Model settings updated!")

with tab_observability:
    st.markdown("### LangSmith Tracing")
    default_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY", "")
    langchain_key_input = st.text_input(
        "LangSmith API Key",
        value=get_state("langchain_api_key", default_key),
        type="password",
    )
    default_tracing = (
        os.getenv("LANGSMITH_TRACING") == "true" or os.getenv("LANGCHAIN_TRACING_V2") == "true"
    )
    tracing_enabled = st.checkbox(
        "Enable Tracing", value=get_state("tracing_enabled", default_tracing)
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
                with open(env_file) as f:
                    lines = [
                        line
                        for line in f.readlines()
                        if not line.startswith("LANGCHAIN_API_KEY=")
                        and not line.startswith("LANGCHAIN_PROJECT=")
                        and not line.startswith("LANGCHAIN_TRACING_V2=")
                        and not line.startswith("LANGSMITH_")
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
        st.success(f"LangSmith Tracing set to: {tracing_enabled}")

with tab_dev:
    st.markdown("### Developer Options & Session Management")
    c1, c2 = st.columns(2)

    with c1:
        if st.button("Clear Chat Messages", use_container_width=True):
            set_state("messages", [])
            st.success("Chat messages cleared!")

    with c2:
        if st.button("Reset Entire Dataset Session", type="primary", use_container_width=True):
            clear_dataset_session()
            st.success("Session state reset!")
            st.rerun()

render_footer()
