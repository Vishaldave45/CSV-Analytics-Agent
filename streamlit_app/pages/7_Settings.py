"""Page 7: Runtime & Observability Configuration Settings."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.services.session import clear_dataset_session, get_state, set_state

st.set_page_config(
    page_title="Settings — LOGIC_OS_2.0",
    page_icon="⚙️",
    layout="wide",
)

render_sidebar()

st.markdown("## ⚙️ Application & Runtime Settings")
st.write("---")

# Model Settings
st.markdown("### 🤖 LLM Model Settings")
model_name = st.selectbox(
    "Gemini Model Name",
    options=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"],
    index=0,
)
temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
max_iterations = st.number_input("Max Loop Iterations", min_value=1, max_value=20, value=6, step=1)

if st.button("Save Model Settings"):
    set_state("model_name", model_name)
    set_state("temperature", temperature)
    set_state("max_iterations", max_iterations)
    st.success("Model settings updated!")

st.write("---")

# Observability Settings
st.markdown("### 📡 LangSmith Observability")
tracing_enabled = st.checkbox("Enable LangSmith Tracing", value=get_state("tracing_enabled", False))

if st.button("Save Observability Settings"):
    set_state("tracing_enabled", tracing_enabled)
    st.success(f"LangSmith Tracing set to: {tracing_enabled}")

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
