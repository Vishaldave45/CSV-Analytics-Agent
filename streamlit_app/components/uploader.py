"""Uploader component matching PAGE 1 Landing Page layout."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from streamlit_app.config import EXAMPLE_QUESTIONS, SAMPLE_DATA_DIR, SAMPLE_DATASETS
from streamlit_app.services.backend import (
    generate_insights_for_dataset,
    load_dataset_from_bytes,
    profile_dataset,
    recommend_visualizations_for_dataset,
)
from streamlit_app.services.session import set_state


def process_loaded_dataframe(df: pd.DataFrame, filename: str) -> None:
    """Process loaded DataFrame through backend profiling, insights, and chart recommendation pipeline.

    Args:
        df: Loaded pandas DataFrame.
        filename: Name string of loaded dataset.
    """
    profile = profile_dataset(df, dataset_name=filename)
    insights = generate_insights_for_dataset(profile)
    charts = recommend_visualizations_for_dataset(profile, insights=insights)

    set_state("raw_df", df)
    set_state("dataset_name", filename)
    set_state("profile", profile)
    set_state("insights", insights)
    set_state("charts", charts)


def render_uploader() -> None:
    """Render hero CSV dropzone, sample dataset quick loaders, and example question chips."""
    st.markdown(
        """
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 2rem;">
            <h1 class="brand-title" style="font-size: 3.2rem;">LOGIC_OS_2.0</h1>
            <p style="font-size: 1.15rem; color: #94a3b8;">Autonomous Tabular Analytics Agent</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Drop your CSV here or click to browse — up to 500MB",
        type=["csv"],
        key="csv_file_uploader",
    )

    if uploaded_file is not None:
        content = uploaded_file.getvalue()
        filename = uploaded_file.name
        with st.spinner(f"Analyzing '{filename}'..."):
            df = load_dataset_from_bytes(content, filename=filename)
            process_loaded_dataframe(df, filename=filename)
        st.success(f"Loaded '{filename}' ({len(df):,} rows × {len(df.columns)} columns)!")
        st.rerun()

    st.write("")
    sample_hdr_html = (
        '<div style="text-align: center; margin-top: 1.5rem; margin-bottom: 0.8rem; '
        'font-size: 0.85rem; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">'
        "OR TRY A SAMPLE DATASET</div>"
    )
    st.markdown(sample_hdr_html, unsafe_allow_html=True)

    cols = st.columns(len(SAMPLE_DATASETS))
    for idx, sample_info in enumerate(SAMPLE_DATASETS):
        with cols[idx]:
            if st.button(f"{sample_info['icon']} {sample_info['name']}", key=f"btn_sample_{idx}", use_container_width=True):
                file_path = SAMPLE_DATA_DIR / sample_info["name"]
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    process_loaded_dataframe(df, filename=sample_info["name"])
                    st.rerun()

    st.write("")
    st.markdown(
        '<div style="text-align: center; margin-top: 1.5rem; margin-bottom: 0.8rem; '
        'font-size: 0.85rem; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">'
        "EXAMPLE QUESTIONS YOU CAN ASK</div>",
        unsafe_allow_html=True,
    )

    ex_cols = st.columns(len(EXAMPLE_QUESTIONS))
    for idx, q_text in enumerate(EXAMPLE_QUESTIONS):
        with ex_cols[idx]:
            st.button(f"💡 {q_text}", key=f"btn_ex_home_{idx}", use_container_width=True)

    st.markdown(
        """
        <div style="text-align: center; margin-top: 2.5rem; color: #64748b; font-size: 0.8rem;">
            🔒 Your data stays local — evaluated deterministically using clean execution engines.
        </div>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["render_uploader"]
