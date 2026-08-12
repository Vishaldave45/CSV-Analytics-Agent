"""Streamlit renderer for the unified AgentResponse model."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from csv_analytics_agent.models.response import AgentResponse, AgentResponseType
from streamlit_app.components.artifact_renderer import render_artifact
from streamlit_app.components.evidence import render_evidence_drawer
from streamlit_app.components.suggested_questions import render_contextual_suggestions


def render_agent_response(
    response: AgentResponse,
    row_count: int | None = None,
    on_select_followup: Callable[[str], None] | None = None,
    msg_index: int = 0,
    is_last: bool = False,
) -> None:
    """Render a canonical AgentResponse within a Streamlit chat message context.

    Args:
        response: The unified AgentResponse model.
        row_count: Optional row count of the dataset for the trust drawer.
        on_select_followup: Optional callback for follow-up suggestion clicks.
        msg_index: Index of this message in the conversation (for unique widget keys).
        is_last: Whether this is the most recent assistant message.
    """
    # 1. Render Error State
    if response.type == AgentResponseType.ERROR:
        st.error(response.error or "Something went wrong.")
        if response.answer:
            st.markdown(response.answer)
        if response.calculation:
            with st.expander("Technical details", expanded=False):
                st.caption(response.calculation)
        return

    # 2. Render Text / Answer Narrative
    if response.answer:
        st.markdown(response.answer)

    # 3. Render Artifacts (Table, Chart, Scalar, Images, etc.)
    has_artifacts = False

    rendered_ids: set[str] = set()

    if response.artifacts:
        for artifact in response.artifacts:
            art_id = getattr(artifact, "artifact_id", None) or str(id(artifact))
            if art_id not in rendered_ids:
                st.write("")
                render_artifact(artifact)
                rendered_ids.add(art_id)
                has_artifacts = True
    else:
        if response.table:
            st.write("")
            render_artifact(response.table)
            has_artifacts = True

        if response.visualization:
            st.write("")
            render_artifact(response.visualization)
            has_artifacts = True

    # 4. Render Insights
    if response.insights:
        st.markdown("#### Key Insights")
        for insight in response.insights:
            st.markdown(f"- {insight}")

    # 5. Render Evidence Drawer (Metadata & Calculation)
    metadata = response.metadata.copy()
    if response.calculation:
        metadata["calculation_note"] = response.calculation

    # We only render the evidence drawer if there's actual data operation evidence
    # Chitchat and Clarification typically don't have execution metadata.
    if (
        response.type not in (AgentResponseType.TEXT, AgentResponseType.CLARIFICATION)
        or has_artifacts
        or metadata.get("executed_tools")
    ):
        render_evidence_drawer(metadata=metadata, row_count=row_count)

    # 6. Render Suggestions — ONLY on the latest assistant message
    if not is_last:
        return

    if response.suggestions:
        # Re-use existing suggestions layout with hardcoded suggestions if provided
        st.write("")
        cols = st.columns(len(response.suggestions))
        for i, suggestion in enumerate(response.suggestions):
            with cols[i]:
                if st.button(
                    suggestion,
                    key=f"suggestion_btn_{msg_index}_{i}_{hash(suggestion)}",
                    use_container_width=True,
                ):
                    if on_select_followup:
                        on_select_followup(suggestion)
    elif response.answer and response.type not in (
        AgentResponseType.CLARIFICATION,
        AgentResponseType.ERROR,
    ):
        # Fall back to dynamic contextual suggestions
        render_contextual_suggestions(
            response.answer,
            on_select=on_select_followup,
            key_prefix=f"msg_{msg_index}",
        )


__all__ = ["render_agent_response"]
