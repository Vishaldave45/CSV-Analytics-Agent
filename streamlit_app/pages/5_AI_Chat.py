"""Page 5: Data Studio Chat Workspace."""

from __future__ import annotations

import logging
import os

import streamlit as st

from csv_analytics_agent.exceptions.data_errors import CSVAnalyticsError
from csv_analytics_agent.llm.gemini import DEFAULT_MODEL_NAME
from streamlit_app.components.chat_box import render_chat_messages
from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.backend import ask_agent, get_or_create_runtime
from streamlit_app.services.session import consume_pending_prompt, get_state, set_state
from streamlit_app.theme import apply_custom_theme

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"Chat — {APP_TITLE}",
    page_icon="💬",
    layout="wide",
)

apply_custom_theme()
render_sidebar()

df = get_state("raw_df")
profile = get_state("profile")
dataset_name = get_state("dataset_name", "Dataset")
dataset_hash = get_state("dataset_hash") or "default_hash"
thread_id = get_state("thread_id")
messages = get_state("messages", [])
model_name = get_state("model_name", DEFAULT_MODEL_NAME)
max_iterations = get_state("max_iterations", 6)
google_api_key = get_state("google_api_key") or os.getenv("GOOGLE_API_KEY", "")

render_header("Chat Workspace", icon="💬")

if not google_api_key:
    st.warning(
        "⚠️ **Gemini API Key Required**: Please enter your Google AI Studio API key on the **Settings** page to enable AI chat queries."
    )

if df is None:
    st.warning("⚠️ No dataset loaded yet. Please upload a CSV file on the home page.")
    st.stop()

# Cache process-level AgentRuntime
runtime = get_or_create_runtime(
    dataset_hash=dataset_hash,
    model_name=model_name,
    max_iterations=max_iterations,
    api_key=google_api_key,
    _df=df,
)

# Active Dataset Bar
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 0.6rem 1rem; margin-bottom: 1.25rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem; font-size: 0.85rem;">
            <span style="color: #64748b; font-weight: 500;">DATASET:</span>
            <span style="color: #38bdf8; font-weight: 600;">{dataset_name}</span>
            <span style="color: #94a3b8;">({len(df):,} rows × {len(df.columns)} cols)</span>
        </div>
        <div>
            <span class="studio-badge studio-badge-success">● Active</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def run_query_pipeline(prompt_text: str) -> None:
    """Execute query prompt through cached AgentRuntime and update UI state."""
    messages.append({"role": "user", "content": prompt_text})
    set_state("messages", messages)

    with st.spinner("Analyzing dataset..."):
        try:
            agent_response = ask_agent(
                runtime,
                prompt=prompt_text,
                thread_id=thread_id,
                profile=profile,
            )

            messages.append(
                {
                    "role": "assistant",
                    "agent_response": agent_response,
                }
            )
            set_state("messages", messages)
            # Retain any context needed for followups if we were tracking them in state
            set_state("last_result", agent_response)

        except CSVAnalyticsError as domain_err:
            logger.exception("Domain error during agent query for thread %s", thread_id)
            from csv_analytics_agent.models.response import AgentResponse, AgentResponseType

            domain_resp = AgentResponse(
                type=AgentResponseType.ERROR,
                error=f"⚠️ {domain_err}",
                answer="I couldn't process your dataset operation.",
                metadata={"thread_id": thread_id},
            )

            messages.append(
                {
                    "role": "assistant",
                    "agent_response": domain_resp,
                }
            )
            set_state("messages", messages)
        except Exception as err:
            logger.exception("Unexpected error during agent query for thread %s", thread_id)
            err_text = str(err)
            if "429" in err_text or "RESOURCE_EXHAUSTED" in err_text or "quota" in err_text.lower():
                display_msg = (
                    "⚠️ **Rate Limit / Quota Exceeded (429)**\n\n"
                    f"The selected model (`{model_name}`) has temporarily reached its API quota limit.\n"
                    "Please wait a few seconds and try your request again."
                )
            else:
                display_msg = "⚠️ Something went wrong while analyzing your data."

            from csv_analytics_agent.models.response import AgentResponse, AgentResponseType

            error_resp = AgentResponse(
                type=AgentResponseType.ERROR,
                error=display_msg,
                answer="I couldn't complete that analysis.",
                metadata={"thread_id": thread_id},
            )

            messages.append(
                {
                    "role": "assistant",
                    "agent_response": error_resp,
                }
            )
            set_state("messages", messages)

    st.rerun()


# Render Chat Messages with follow-up callback
render_chat_messages(messages, df, on_select_followup=run_query_pipeline)

# Chat Input Composer
user_query = st.chat_input(
    "Ask anything about your dataset... e.g. 'top 5 categories by total revenue'"
)

# Check if there is a pending prompt from quick suggestion chip or a direct chat input submission
submitted_prompt = consume_pending_prompt(user_query)

if submitted_prompt:
    run_query_pipeline(submitted_prompt)

render_footer()
