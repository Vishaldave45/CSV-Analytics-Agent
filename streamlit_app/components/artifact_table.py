"""Streamlit renderer component for TABLE and DATAFRAME artifacts in Quiet Data Studio."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from csv_analytics_agent.results.models import AnalysisArtifact


def render_table(artifact: AnalysisArtifact | dict[str, Any]) -> None:
    """Render a tabular or DataFrame artifact inside Streamlit.

    Args:
        artifact: AnalysisArtifact model or dictionary representation.
    """
    payload: Any = None
    title: str | None = None
    description: str | None = None
    name: str = "data_table"
    row_count: int | None = None
    column_count: int | None = None

    if isinstance(artifact, dict):
        payload = artifact.get("payload")
        title = artifact.get("title")
        description = artifact.get("description")
        name = artifact.get("name", "data_table")
        meta = artifact.get("metadata", {})
        row_count = meta.get("row_count")
        column_count = meta.get("column_count")
    else:
        payload = artifact.payload
        title = artifact.title or artifact.name.replace("_", " ").title()
        description = artifact.description
        name = artifact.name
        row_count = artifact.metadata.get("row_count")
        column_count = artifact.metadata.get("column_count")

    if title:
        st.markdown(f"##### {title}")
    if description:
        st.caption(description)

    # Resolve pandas DataFrame representation
    df: pd.DataFrame | None = None

    if isinstance(payload, pd.DataFrame):
        df = payload
    elif isinstance(payload, pd.Series):
        df = payload.to_frame()
    elif isinstance(payload, dict):
        if "preview" in payload and isinstance(payload["preview"], dict):
            p_dict = payload["preview"]
            cols = p_dict.get("columns", [])
            idx = p_dict.get("index", [])
            data = p_dict.get("data", [])
            try:
                df = pd.DataFrame(data, index=idx if idx else None, columns=cols if cols else None)
            except Exception:
                df = None
        elif "columns" in payload and "data" in payload:
            try:
                df = pd.DataFrame(payload["data"], columns=payload["columns"])
            except Exception:
                df = None
        else:
            try:
                df = pd.DataFrame(payload)
            except Exception:
                try:
                    df = pd.DataFrame([payload])
                except Exception:
                    try:
                        df = pd.DataFrame(list(payload.items()), columns=["Key", "Value"])
                    except Exception:
                        df = None
    elif isinstance(payload, list):
        try:
            df = pd.DataFrame(payload)
        except Exception:
            try:
                df = pd.json_normalize(payload)
            except Exception:
                df = None

    if df is not None and not df.empty:
        r_cnt = row_count or len(df)
        c_cnt = column_count or len(df.columns)
        st.caption(f"{r_cnt} rows × {c_cnt} columns")

        st.dataframe(df, use_container_width=True)

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"Download {name}.csv",
            data=csv_bytes,
            file_name=f"{name}.csv",
            mime="text/csv",
            key=f"dl_table_{name}_{hash(str(payload))}",
        )
    else:
        st.info("No tabular data available in artifact payload.")


__all__ = ["render_table"]
