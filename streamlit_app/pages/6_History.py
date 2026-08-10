"""Page 6: Conversation History & Saved Threads."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.session import get_state, set_state
from streamlit_app.theme import apply_custom_theme

st.set_page_config(
    page_title=f"History — {APP_TITLE}",
    page_icon="📜",
    layout="wide",
)

apply_custom_theme()
render_sidebar()

thread_id = get_state("thread_id")
messages = get_state("messages", [])

render_header("Conversation History", icon="📜")

st.caption(f"Active Thread ID: `{thread_id}`")
st.write("---")

if not messages:
    st.info("No conversation history recorded in current session.")
else:
    st.markdown(f"### Thread `{thread_id}` ({len(messages)} messages)")
    for _idx, msg in enumerate(messages):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        st.markdown(f"**[{role.upper()}]**: {content}")

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Resume Current Thread", type="primary", use_container_width=True):
            st.success(f"Resumed thread {thread_id}")
    with col2:
        if st.button("Clear Thread Messages", use_container_width=True):
            set_state("messages", [])
            st.success("Messages cleared.")
            st.rerun()

render_footer()
