"""Page 5: Conversational AI Agent Chat & Execution Timeline matching StitchMCP."""

from __future__ import annotations

import logging
import os

import streamlit as st

from csv_analytics_agent.exceptions.data_errors import CSVAnalyticsError
from csv_analytics_agent.llm.gemini import DEFAULT_MODEL_NAME
from streamlit_app.components.chat_box import render_chat_messages
from streamlit_app.components.followup_buttons import render_followup_buttons
from streamlit_app.components.footer import render_footer
from streamlit_app.components.header import render_header
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.config import APP_TITLE
from streamlit_app.services.backend import ask_agent, get_or_create_runtime
from streamlit_app.services.session import get_state, set_state
from streamlit_app.theme import apply_custom_theme

logger = logging.getLogger(__name__)

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
dataset_hash = get_state("dataset_hash") or "default_hash"
thread_id = get_state("thread_id")
messages = get_state("messages", [])
model_name = get_state("model_name", DEFAULT_MODEL_NAME)
max_iterations = get_state("max_iterations", 6)
google_api_key = get_state("google_api_key") or os.getenv("GOOGLE_API_KEY", "")

render_header("Conversational Analytics", icon="🤖")

if not google_api_key:
    st.warning(
        "⚠️ **Gemini API Key Required**: Please enter your Google AI Studio API key on the **Settings** page to enable AI chat queries."
    )

if df is None:
    st.warning("⚠️ No dataset loaded yet. Please upload a CSV file on the Upload page.")
    st.stop()

# --- AgentRuntime: process-level cache via st.cache_resource keyed on dataset_hash + config ---
runtime = get_or_create_runtime(
    dataset_hash=dataset_hash,
    model_name=model_name,
    max_iterations=max_iterations,
    api_key=google_api_key,
    _df=df,
)

# Active Dataset & Filter Command Bar
active_filters = get_state("active_filters", [])

st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(14, 14, 18, 0.8); border: 1px solid #1e293b; border-radius: 10px; padding: 0.6rem 1rem; margin-bottom: 1.25rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem; font-family: var(--font-mono); font-size: 0.82rem;">
            <span style="color: #869397;">ACTIVE DATASET:</span>
            <span style="color: #4cd7f6; font-weight: 600;">{dataset_name}</span>
            <span style="color: #869397;">({len(df):,} rows × {len(df.columns)} cols)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="badge badge-optimal">READY</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if active_filters:
    col_f1, col_f2 = st.columns([4, 1])
    with col_f1:
        st.info(f"Active Filters: {active_filters}")
    with col_f2:
        if st.button("Reset Filters", key="btn_reset_chat_filters", use_container_width=True):
            set_state("active_filters", [])
            st.rerun()

# Render Chat Messages
render_chat_messages(messages, df)

# Chat Input Box
user_query = st.chat_input("Ask a question about your data... e.g. 'top 5 products by revenue'")


def run_query_pipeline(prompt_text: str) -> None:
    """Execute query prompt through the cached AgentRuntime and update UI state."""
    messages.append({"role": "user", "content": prompt_text})
    set_state("messages", messages)

    with st.spinner("🧠 LOGIC_OS evaluating deterministic query plan..."):
        try:
            result_state = ask_agent(
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
                    last_msg_text = (
                        f"✅ {last_result.message}"
                        if hasattr(last_result, "message")
                        else str(last_result)
                    )
                else:
                    last_msg_text = "⚠️ The agent completed but produced no result. Please try rephrasing your question."

            # Extract aligned orchestration metadata
            planner_result = result_state.get("planner_result")
            retrieved_cols = result_state.get("retrieved_columns") or []
            iteration_count = result_state.get("iteration_count", 1)
            executed_tools = result_state.get("executed_tools") or []

            cap_name = "analytics.query"
            if last_result is not None:
                cap_name = last_result.capability_name
            elif executed_tools:
                cap_name = executed_tools[-1]
            elif planner_result is not None:
                exec_req = getattr(planner_result, "execution_request", None)
                if exec_req is not None:
                    cap_name = getattr(exec_req, "capability_name", cap_name)

            if cap_name in ("render_visualization", "recommend_visualization"):
                engine_name = "VisualizationProvider"
            elif cap_name in ("aggregate", "filter", "group", "sort", "top_n"):
                engine_name = "PandasProvider"
            else:
                engine_name = "LogicEngine"

            planner_rule = cap_name if cap_name != "analytics.query" else "direct_query"

            metadata = {
                "router_node": "analytics_query",
                "planner_rule": planner_rule,
                "tool_name": cap_name,
                "engine_provider": engine_name,
                "retrieved_columns": retrieved_cols if retrieved_cols else list(df.columns[:2]),
                "iteration_count": iteration_count,
                "thread_id": thread_id,
            }

            # Extract chart image bytes from result_state or last_result
            image_bytes: bytes | None = result_state.get("chart_bytes")
            if image_bytes is None and last_result is not None:
                if isinstance(last_result.data, bytes):
                    image_bytes = last_result.data
                elif hasattr(last_result.data, "primary"):
                    try:
                        from csv_analytics_agent.visualization.renderer import render_chart

                        image_bytes = render_chart(last_result.data.primary, df)
                    except Exception:
                        pass
                elif hasattr(last_result.data, "chart_type"):
                    try:
                        from csv_analytics_agent.visualization.renderer import render_chart

                        image_bytes = render_chart(last_result.data, df)
                    except Exception:
                        pass

            data_str = (
                str(last_result)
                if last_result is not None and not isinstance(last_result.data, bytes)
                else None
            )

            messages.append(
                {
                    "role": "assistant",
                    "content": last_msg_text,
                    "metadata": metadata,
                    "data": data_str,
                    "image": image_bytes,
                }
            )
            set_state("messages", messages)
            set_state("last_result", last_result)
            set_state("active_filters", result_state.get("active_filters", []))

        except CSVAnalyticsError as domain_err:
            logger.exception("Domain error during agent query for thread %s", thread_id)
            messages.append(
                {
                    "role": "assistant",
                    "content": f"⚠️ {domain_err}",
                    "metadata": {
                        "router_node": "⚡ DOMAIN ERROR",
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
        except Exception as err:
            logger.exception("Unexpected error during agent query for thread %s", thread_id)
            err_text = str(err)
            if "429" in err_text or "RESOURCE_EXHAUSTED" in err_text or "quota" in err_text.lower():
                display_msg = (
                    "⚠️ **Gemini Free Tier Rate Limit / Quota Exceeded (429)**\n\n"
                    f"The selected model (`{model_name}`) has temporarily reached its Google AI rate limit or quota.\n\n"
                    "💡 **Suggested solutions:**\n"
                    f"1. Go to **Settings** and switch model to **`{DEFAULT_MODEL_NAME}`** or **`gemini-flash-latest`**.\n"
                    "2. Wait ~30–60 seconds for the free-tier rate limit bucket to refill, then retry."
                )
            else:
                display_msg = f"⚠️ **Execution Exception**: {err}"

            messages.append(
                {
                    "role": "assistant",
                    "content": display_msg,
                    "metadata": {
                        "router_node": "⚡ EXECUTION ERROR",
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


# Check if there is a pending prompt from quick suggestion chip
pending_prompt = get_state("pending_prompt")
if pending_prompt:
    set_state("pending_prompt", None)
    run_query_pipeline(pending_prompt)

if user_query:
    run_query_pipeline(user_query)

render_followup_buttons(on_select=run_query_pipeline)
render_footer()
