"""Dataframe viewer component with export options."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_dataframe_view(
    df: pd.DataFrame, title: str = "Data Preview", max_rows: int = 20
) -> None:
    """Render interactive DataFrame view with dimensions and CSV export."""
    st.markdown(f"### 📄 {title}")
    st.caption(
        f"Showing top {min(max_rows, len(df))} of {len(df):,} total rows × {len(df.columns)} columns"
    )
    st.dataframe(df.head(max_rows), use_container_width=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Results CSV",
        data=csv_bytes,
        file_name="analytics_result.csv",
        mime="text/csv",
        key=f"btn_dl_csv_{hash(title)}",
    )


__all__ = ["render_dataframe_view"]
