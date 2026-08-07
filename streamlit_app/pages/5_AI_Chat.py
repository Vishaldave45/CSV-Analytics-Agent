"""Page 5: Conversational AI Agent Chat & Execution Timeline."""

from __future__ import annotations

import streamlit as st

from streamlit_app.components.chat_box import (
    render_chat_messages,
    render_suggested_followups,
)
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.services.backend import create_agent_runtime, execute_agent_query
from streamlit_app.services.session import get_state, set_state

st.set_page_config(
    page_title="AI Chat — LOGIC_OS_2.0",
    page_icon="🤖",
    layout="wide",
)

render_sidebar()

df = get_state("raw_df")
dataset_name = get_state("dataset_name", "Dataset")
thread_id = get_state("thread_id")
messages = get_state("messages", [])
model_name = get_state("model_name", "gemini-1.5-flash")
max_iterations = get_state("max_iterations", 6)

st.markdown(f"## 🤖 AI Analytics Agent: `{dataset_name}`")

if df is None:
    st.warning("No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

# Render existing chat message history
render_chat_messages(messages, df)

# Handle user input query
user_query = st.chat_input("Ask a question about your data... e.g. 'top 5 products by revenue'")


def run_query_pipeline(prompt_text: str) -> None:
    """Execute query prompt through AgentRuntime and update UI chat messages.

    Args:
        prompt_text: Input query string.
    """
    messages.append({"role": "user", "content": prompt_text})
    set_state("messages", messages)

    with st.spinner("Logic Engine executing query plan..."):
        try:
            runtime = create_agent_runtime(
                df=df,
                model_name=model_name,
                max_iterations=max_iterations,
            )
            result_state = execute_agent_query(runtime, prompt=prompt_text, thread_id=thread_id)

            # Extract response message text
            response_msgs = result_state.get("messages", [])
            last_msg_text = "Analysis complete."
            if response_msgs:
                last_msg_text = getattr(response_msgs[-1], "content", str(response_msgs[-1]))

            # Extract execution steps
            steps = ["Router", "Retrieval", "Planner"]
            if result_state.get("last_result"):
                steps.extend(["Tool", "Explainer", "MemoryUpdate"])
            else:
                steps.append("Explainer")

            messages.append(
                {
                    "role": "assistant",
                    "content": last_msg_text,
                    "execution_steps": steps,
                    "data": str(result_state.get("last_result")),
                }
            )
            set_state("messages", messages)
            set_state("last_result", result_state.get("last_result"))
            set_state("active_filters", result_state.get("active_filters", []))

        except Exception as err:
            messages.append(
                {
                    "role": "assistant",
                    "content": f"⚠️ Execution Exception: {err}",
                    "execution_steps": ["Router", "Error"],
                }
            )
            set_state("messages", messages)

    st.rerun()


if user_query:
    run_query_pipeline(user_query)

# Render suggested questions chips at bottom
render_suggested_followups(on_select=run_query_pipeline)
