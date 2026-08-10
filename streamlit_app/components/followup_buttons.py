"""Suggested quick follow-up questions chip component matching Stitch layout."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from streamlit_app.config import EXAMPLE_QUESTIONS


def render_followup_buttons(on_select: Callable[[str], None] | None = None) -> None:
    """Render suggested quick question chips at bottom of chat screen.

    Args:
        on_select: Optional callback triggered when user selects a chip.
    """
    st.write("")
    st.markdown(
        '<div style="font-family: var(--font-mono); font-size: 0.72rem; color: #869397; '
        'text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">'
        "SUGGESTED QUICK QUERIES</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(EXAMPLE_QUESTIONS))
    for idx, q_text in enumerate(EXAMPLE_QUESTIONS):
        with cols[idx]:
            if st.button(f"⚡ {q_text}", key=f"chip_q_{idx}", use_container_width=True):
                if on_select:
                    on_select(q_text)


__all__ = ["render_followup_buttons"]
