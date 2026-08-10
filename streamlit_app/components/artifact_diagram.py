"""Streamlit renderer component for DIAGRAM artifacts."""

from __future__ import annotations

from typing import Any

import streamlit as st

from csv_analytics_agent.results.models import AnalysisArtifact


def render_diagram(artifact: AnalysisArtifact | dict[str, Any]) -> None:
    """Render a DIAGRAM (Mermaid/SVG/Graphviz) artifact inside Streamlit.

    Args:
        artifact: AnalysisArtifact model or dictionary serialized representation.
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
        st.markdown(f"#### 🔷 {title}")
    if description:
        st.caption(description)

    if payload is None:
        st.info("No diagram payload available.")
        return

    # Mermaid diagram string representation
    if isinstance(payload, str):
        if (
            payload.strip().startswith("graph")
            or payload.strip().startswith("sequenceDiagram")
            or payload.strip().startswith("flowchart")
        ):
            st.markdown(f"```mermaid\n{payload.strip()}\n```")
        else:
            st.code(payload, language="text")
    elif isinstance(payload, dict):
        st.json(payload)
    else:
        st.warning(f"Fallback diagram representation: {payload}")


__all__ = ["render_diagram"]
