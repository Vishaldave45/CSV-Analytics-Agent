"""Loading and status animation indicators."""

from __future__ import annotations

import contextlib
from typing import Iterator

import streamlit as st


@contextlib.contextmanager
def render_loading_state(message: str = "Analyzing dataset...") -> Iterator[None]:
    """Context manager for rendering a sleek loading status indicator."""
    with st.spinner(f"🧠 {message}"):
        yield


__all__ = ["render_loading_state"]
