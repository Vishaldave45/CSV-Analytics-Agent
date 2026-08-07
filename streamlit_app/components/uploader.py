"""Uploader component matching LOGIC_OS_2.0 hero upload screen."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from streamlit_app.services.backend import (
    generate_insights_for_dataset,
    load_dataset_from_bytes,
    profile_dataset,
    recommend_visualizations_for_dataset,
)
from streamlit_app.services.session import set_state

SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"


def process_loaded_dataframe(df: pd.DataFrame, filename: str) -> None:
    """Process loaded DataFrame through profiling, insights, and chart recommendation pipeline.

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
    """Render LOGIC_OS_2.0 hero CSV dropzone and sample dataset quick loaders."""
    st.markdown(
        """
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 2rem;">
            <h1 class="brand-title" style="font-size: 3rem;">LOGIC_OS_2.0</h1>
            <p style="font-size: 1.1rem; color: #94a3b8;">Ask your data anything.</p>
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
        with st.spinner(f"Processing '{filename}'..."):
            df = load_dataset_from_bytes(content, filename=filename)
            process_loaded_dataframe(df, filename=filename)
        st.success(f"Loaded '{filename}' ({len(df)} rows × {len(df.columns)} columns)!")
        st.rerun()

    st.write("")
    sample_hdr_html = (
        '<div style="text-align: center; margin-top: 1.5rem; margin-bottom: 0.8rem; '
        'font-size: 0.85rem; color: #64748b; font-weight: 600; letter-spacing: 0.05em;">'
        "OR TRY A SAMPLE DATASET</div>"
    )
    st.markdown(sample_hdr_html, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Sales Data", use_container_width=True):
            file_path = SAMPLE_DATA_DIR / "sales_data.csv"
            if file_path.exists():
                df = pd.read_csv(file_path)
                process_loaded_dataframe(df, filename="sales_data.csv")
                st.rerun()

    with col2:
        if st.button("👥 Customer Churn", use_container_width=True):
            file_path = SAMPLE_DATA_DIR / "customer_churn.csv"
            if file_path.exists():
                df = pd.read_csv(file_path)
                process_loaded_dataframe(df, filename="customer_churn.csv")
                st.rerun()

    with col3:
        if st.button("💬 Survey Responses", use_container_width=True):
            file_path = SAMPLE_DATA_DIR / "survey_responses.csv"
            if file_path.exists():
                df = pd.read_csv(file_path)
                process_loaded_dataframe(df, filename="survey_responses.csv")
                st.rerun()

    st.markdown(
        """
        <div style="text-align: center; margin-top: 2.5rem; color: #64748b; font-size: 0.8rem;">
            🔒 Your data stays local — evaluated deterministically using clean execution engines.
        </div>
        """,
        unsafe_allow_html=True,
    )


__all__ = ["render_uploader"]
