"""Page 6: Checkpointed Session History & Execution Log Table."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.services.session import get_state

st.set_page_config(
    page_title="History — LOGIC_OS_2.0",
    page_icon="📜",
    layout="wide",
)

render_sidebar()

thread_id = get_state("thread_id")
messages = get_state("messages", [])
last_result = get_state("last_result")

st.markdown("## 📜 Conversation & Execution History")
st.caption(f"Session Thread ID: `{thread_id}`")
st.write("---")

if not messages:
    st.info("No query execution history found in current session.")
    st.stop()

st.markdown("### 💬 Message Log")
for idx, msg in enumerate(messages):
    role = msg.get("role", "unknown")
    content = msg.get("content", "")
    st.markdown(f"**[{idx + 1}] {role.upper()}**: {content}")

if last_result:
    st.write("---")
    st.markdown("### ⚡ Latest Execution Result Payload")
    st.json(
        {
            "capability": last_result.capability_name,
            "status": last_result.status.value,
            "message": last_result.message,
            "execution_time_ms": last_result.execution_time_ms,
            "metadata": last_result.metadata,
        }
    )
