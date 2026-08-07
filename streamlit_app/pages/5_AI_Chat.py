"""Page 5: Conversational AI Agent Chat & Execution Timeline."""

from __future__ import annotations

import os

import streamlit as st

from streamlit_app.components.chat_box import render_chat_messages
from streamlit_app.components.followup_buttons import render_followup_buttons
from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.backend import create_agent_runtime, execute_agent_query
from streamlit_app.services.session import get_state, set_state
from streamlit_app.theme import apply_custom_theme

st.set_page_config(
    page_title=f"AI Chat — {APP_TITLE}",
    page_icon="🤖",
    layout="wide",
)

apply_custom_theme()
render_sidebar()

df = get_state("raw_df")
profile = get_state("profile")
dataset_name = get_state("dataset_name", "Dataset")
thread_id = get_state("thread_id")
messages = get_state("messages", [])
model_name = get_state("model_name", "gemini-2.5-flash")
max_iterations = get_state("max_iterations", 6)
google_api_key = get_state("google_api_key") or os.getenv("GOOGLE_API_KEY", "")

render_header("AI Analytics Agent", icon="🤖")

if not google_api_key:
    st.warning("⚠️ **Gemini API Key Required**: Please enter your Google AI Studio API key on the **Settings** page to enable AI chat queries.")

if df is None:
    st.warning("No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

# Active Filters Header Bar
active_filters = get_state("active_filters", [])
if active_filters:
    col_f1, col_f2 = st.columns([4, 1])
    with col_f1:
        st.info(f"Active Filters: {active_filters}")
    with col_f2:
        if st.button("Reset Filters", key="btn_reset_chat_filters"):
            set_state("active_filters", [])
            st.rerun()

# Render Chat Messages
render_chat_messages(messages, df)

# Chat Input Box
user_query = st.chat_input("Ask a question about your data... e.g. 'top 5 products by revenue'")


def run_query_pipeline(prompt_text: str) -> None:
    """Execute query prompt through AgentRuntime and update UI state."""
    messages.append({"role": "user", "content": prompt_text})
    set_state("messages", messages)

    with st.spinner("Logic Engine executing query plan..."):
        try:
            runtime = create_agent_runtime(
                df=df,
                model_name=model_name,
                max_iterations=max_iterations,
                api_key=google_api_key,
            )
            result_state = execute_agent_query(
                runtime,
                prompt=prompt_text,
                thread_id=thread_id,
                profile=profile,
            )

            response_msgs = result_state.get("messages", [])
            last_result = result_state.get("last_result")

            # Build response content from last message or last_result
            last_msg_text = "Analysis complete."
            if response_msgs:
                last_msg = response_msgs[-1]
                last_msg_text = getattr(last_msg, "content", str(last_msg))

            if not last_msg_text or last_msg_text.strip() in ("", "Analysis complete."):
                if last_result is not None:
                    last_msg_text = f"✅ {last_result.message}" if hasattr(last_result, "message") else str(last_result)
                else:
                    last_msg_text = "⚠️ The agent completed but produced no result. Please try rephrasing your question."

            # Extract real metadata from result_state
            planner_result = result_state.get("planner_result")
            retrieved_cols = result_state.get("retrieved_columns") or []
            iteration_count = result_state.get("iteration_count", 1)

            cap_name = "unknown"
            planner_rule = "unknown"
            engine_name = "unknown"
            if planner_result is not None:
                planner_rule = getattr(planner_result, "matched_rule", None) or "unknown"
                exec_req = getattr(planner_result, "execution_request", None)
                if exec_req is not None:
                    cap_name = getattr(exec_req, "capability_name", "unknown")
            if last_result is not None:
                cap_name = getattr(last_result, "capability_name", cap_name)

            metadata = {
                "router_node": "analytics_query",
                "planner_rule": planner_rule,
                "tool_name": cap_name,
                "engine_provider": engine_name,
                "retrieved_columns": retrieved_cols if retrieved_cols else list(df.columns[:2]),
                "iteration_count": iteration_count,
                "thread_id": thread_id,
            }

            messages.append(
                {
                    "role": "assistant",
                    "content": last_msg_text,
                    "metadata": metadata,
                    "data": str(last_result),
                }
            )
            set_state("messages", messages)
            set_state("last_result", last_result)
            set_state("active_filters", result_state.get("active_filters", []))

        except Exception as err:
            messages.append(
                {
                    "role": "assistant",
                    "content": f"⚠️ Execution Exception: {err}",
                    "metadata": {
                        "router_node": "⚡ ROUTER⚡ ERROR",
                        "planner_rule": "error",
                        "tool_name": "error",
                        "engine_provider": "None",
                        "retrieved_columns": [],
                        "iteration_count": 0,
                        "thread_id": thread_id,
                    },
                }
            )
            set_state("messages", messages)

    st.rerun()



if user_query:
    run_query_pipeline(user_query)

render_followup_buttons(on_select=run_query_pipeline)
render_footer()
