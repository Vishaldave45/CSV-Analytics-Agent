"""Suggested quick follow-up questions chip component."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from streamlit_app.config import EXAMPLE_QUESTIONS


def render_followup_buttons(on_select: Callable[[str], None] | None = None) -> None:
    """Render suggested quick question chips at bottom of chat screen."""
    st.write("")
    st.caption("SUGGESTED QUICK QUESTIONS")

    cols = st.columns(len(EXAMPLE_QUESTIONS))
    for idx, q_text in enumerate(EXAMPLE_QUESTIONS):
        with cols[idx]:
            if st.button(f"💬 {q_text}", key=f"chip_q_{idx}", use_container_width=True):
                if on_select:
                    on_select(q_text)


__all__ = ["render_followup_buttons"]
