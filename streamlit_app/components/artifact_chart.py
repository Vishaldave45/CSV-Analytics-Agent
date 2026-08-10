"""Streamlit renderer component for INTERACTIVE Plotly chart artifacts."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from csv_analytics_agent.results.models import AnalysisArtifact


def render_interactive(artifact: AnalysisArtifact | dict[str, Any]) -> None:
    """Render an interactive Plotly visualization artifact inside Streamlit.

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
        title = artifact.title or "Interactive Visualization"
        description = artifact.description

    if title:
        st.markdown(f"#### 📈 {title}")
    if description:
        st.caption(description)

    if payload is None:
        st.info("No chart payload available.")
        return

    # 1. Plotly Figure Object
    if hasattr(payload, "to_dict") and callable(payload.to_dict):
        try:
            st.plotly_chart(payload, use_container_width=True)
            return
        except Exception as err:
            st.error(f"Failed to display Plotly figure: {err}")
            return

    # 2. Dictionary / Serialized Plotly Specification
    if isinstance(payload, dict):
        try:
            st.plotly_chart(payload, use_container_width=True)
            return
        except Exception:
            try:
                import plotly.io as pio

                fig = pio.from_json(json.dumps(payload))
                st.plotly_chart(fig, use_container_width=True)
                return
            except Exception as err:
                st.error(f"Unable to render Plotly JSON specification: {err}")
                return

    # 3. String JSON specification
    if isinstance(payload, str) and payload.strip().startswith("{"):
        try:
            dict_spec = json.loads(payload)
            st.plotly_chart(dict_spec, use_container_width=True)
            return
        except Exception as err:
            st.error(f"Failed to parse Plotly JSON string payload: {err}")
            return

    st.warning("Unrecognized Plotly interactive artifact payload format.")


__all__ = ["render_interactive"]
