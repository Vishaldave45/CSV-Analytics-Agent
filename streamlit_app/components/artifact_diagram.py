"""Streamlit renderer component for DIAGRAM artifacts in Quiet Data Studio."""

from __future__ import annotations

from typing import Any

import streamlit as st

from csv_analytics_agent.results.models import AnalysisArtifact


def render_diagram(artifact: AnalysisArtifact | dict[str, Any]) -> None:
    """Render a DIAGRAM (Mermaid/SVG/Graphviz) artifact inside Streamlit safely.

    Args:
        artifact: AnalysisArtifact model or dictionary representation.
    """
    payload: Any = None
    title: str | None = None
    description: str | None = None

    if isinstance(artifact, dict):
        payload = artifact.get("payload")
        title = artifact.get("title")
        description = artifact.get("description")
    else:
        payload = artifact.payload
        title = artifact.title or "Diagram"
        description = artifact.description

    if title:
        st.markdown(f"##### {title}")
    if description:
        st.caption(description)

    if payload is None:
        st.info("No diagram payload available.")
        return

    # Mermaid diagram string representation - sanitized via code block markdown
    if isinstance(payload, str):
        p_strip = payload.strip()
        if (
            p_strip.startswith("graph")
            or p_strip.startswith("sequenceDiagram")
            or p_strip.startswith("flowchart")
            or p_strip.startswith("erDiagram")
        ):
            st.markdown(f"```mermaid\n{p_strip}\n```")
        else:
            st.code(p_strip, language="text")
    elif isinstance(payload, dict):
        st.json(payload)
    else:
        st.warning(f"Fallback diagram representation: {payload}")


__all__ = ["render_diagram"]
