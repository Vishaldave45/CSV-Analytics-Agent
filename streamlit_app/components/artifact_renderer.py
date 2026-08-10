"""Central dynamic Streamlit artifact renderer dispatcher."""

from __future__ import annotations

from typing import Any

import streamlit as st

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import (
    AnalysisArtifact,
    AnalysisResult,
    AnalysisStatus,
)
from streamlit_app.components.artifact_chart import render_interactive
from streamlit_app.components.artifact_diagram import render_diagram
from streamlit_app.components.artifact_file import render_file
from streamlit_app.components.artifact_image import render_image
from streamlit_app.components.artifact_table import render_table


def render_text(payload: Any, title: str | None = None, description: str | None = None) -> None:
    """Render a TEXT artifact."""
    if title:
        st.markdown(f"#### 📝 {title}")
    if description:
        st.caption(description)
    st.markdown(str(payload or ""))


def render_scalar(payload: Any, title: str | None = None, description: str | None = None) -> None:
    """Render a SCALAR artifact as a metric card."""
    label = title or "Scalar Metric"
    if description:
        st.caption(description)

    val_str: str
    if isinstance(payload, (int, float)):
        val_str = f"{payload:,.2f}" if isinstance(payload, float) else f"{payload:,}"
    else:
        val_str = str(payload)

    st.metric(label=label, value=val_str)


def render_fallback(artifact: AnalysisArtifact | dict[str, Any]) -> None:
    """Render fallback for unknown artifact type."""
    st.warning("Unknown artifact type payload.")
    st.json(artifact if isinstance(artifact, dict) else artifact.model_dump())


def render_artifact(artifact: AnalysisArtifact | dict[str, Any]) -> None:
    """Central dispatcher rendering any AnalysisArtifact by its artifact_type.

    Args:
        artifact: AnalysisArtifact model or dictionary representation.
    """
    art_type_raw: Any = None
    title: str | None = None
    description: str | None = None
    payload: Any = None

    if isinstance(artifact, dict):
        art_type_raw = artifact.get("artifact_type")
        title = artifact.get("title")
        description = artifact.get("description")
        payload = artifact.get("payload")
    else:
        art_type_raw = artifact.artifact_type
        title = artifact.title or artifact.name.replace("_", " ").title()
        description = artifact.description
        payload = artifact.payload

    # Normalize type to string or PythonArtifactType
    art_type_str = str(
        art_type_raw.value if hasattr(art_type_raw, "value") else art_type_raw
    ).lower()

    if art_type_str in ("text", PythonArtifactType.TEXT.value):
        render_text(payload, title, description)
    elif art_type_str in ("scalar", PythonArtifactType.SCALAR.value):
        render_scalar(payload, title, description)
    elif art_type_str in (
        "table",
        "dataframe",
        PythonArtifactType.TABLE.value,
        PythonArtifactType.DATAFRAME.value,
    ):
        render_table(artifact)
    elif art_type_str in ("interactive", PythonArtifactType.INTERACTIVE.value):
        render_interactive(artifact)
    elif art_type_str in ("image", PythonArtifactType.IMAGE.value):
        render_image(artifact)
    elif art_type_str in ("diagram", PythonArtifactType.DIAGRAM.value):
        render_diagram(artifact)
    elif art_type_str in ("file", PythonArtifactType.FILE.value):
        render_file(artifact)
    else:
        render_fallback(artifact)


def render_analysis_result(result: AnalysisResult | dict[str, Any]) -> None:
    """Render a complete unified AnalysisResult inside Streamlit.

    Args:
        result: AnalysisResult instance or dict serialized representation.
    """
    narrative: str = ""
    status_str: str = "success"
    artifacts: list[Any] = []
    error_type: str | None = None
    error_message: str | None = None

    if isinstance(result, dict):
        narrative = str(result.get("narrative", ""))
        status_str = str(result.get("status", "success")).lower()
        artifacts = list(result.get("artifacts", []))
        error_type = result.get("error_type")
        error_message = result.get("error_message")
    else:
        narrative = result.narrative
        status_str = result.status.value.lower()
        artifacts = list(result.artifacts)
        error_type = result.error_type
        error_message = result.error_message

    # 1. Render Narrative
    if narrative:
        st.markdown(narrative)

    # 2. Render Status Notifications & Error Details
    if status_str == AnalysisStatus.FAILED.value.lower():
        st.error("I couldn't complete that analysis.")
        if error_message or error_type:
            with st.expander("Technical details", expanded=False):
                st.code(
                    f"Error Type: {error_type or 'Unknown'}\nDetails: {error_message or 'None'}"
                )

    elif status_str == AnalysisStatus.PARTIAL.value.lower():
        st.warning("Analysis completed partially. Some requested outputs could not be generated.")
        if error_message:
            with st.expander("Partial execution details", expanded=False):
                st.caption(f"{error_type}: {error_message}")

    # 3. Render Artifacts sequentially in order
    for art in artifacts:
        render_artifact(art)


__all__ = [
    "render_analysis_result",
    "render_artifact",
    "render_scalar",
    "render_text",
]
