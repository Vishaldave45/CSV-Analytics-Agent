"""Streamlit renderer component for downloadable FILE artifacts in Quiet Data Studio."""

from __future__ import annotations

from typing import Any

import streamlit as st

from csv_analytics_agent.results.models import AnalysisArtifact


def render_file(artifact: AnalysisArtifact | dict[str, Any]) -> None:
    """Render a downloadable FILE artifact inside Streamlit.

    Args:
        artifact: AnalysisArtifact model or dictionary representation.
    """
    payload: Any = None
    title: str | None = None
    description: str | None = None
    name: str = "file.dat"
    mime_type: str = "application/octet-stream"

    if isinstance(artifact, dict):
        payload = artifact.get("payload")
        title = artifact.get("title")
        description = artifact.get("description")
        name = artifact.get("name", "file.dat")
        mime_type = (
            artifact.get("mime_type", "application/octet-stream") or "application/octet-stream"
        )
    else:
        payload = artifact.payload
        title = artifact.title or artifact.name
        description = artifact.description
        name = artifact.name
        mime_type = artifact.mime_type or "application/octet-stream"

    if title:
        st.markdown(f"##### {title}")
    if description:
        st.caption(description)

    data_bytes: bytes = b""
    if isinstance(payload, bytes):
        data_bytes = payload
    elif isinstance(payload, str):
        data_bytes = payload.encode("utf-8")
    elif isinstance(payload, dict):
        data_bytes = str(payload).encode("utf-8")

    size_kb = len(data_bytes) / 1024.0

    st.markdown(
        f"""
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 6px; padding: 0.65rem 0.85rem; margin-bottom: 0.5rem; font-size: 0.82rem; color: #cbd5e1;">
            📄 <strong>{name}</strong> • {mime_type} • {size_kb:.1f} KB
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.download_button(
        label=f"Download {name}",
        data=data_bytes,
        file_name=name,
        mime=mime_type,
        key=f"dl_file_{name}_{hash(name)}",
    )


__all__ = ["render_file"]
