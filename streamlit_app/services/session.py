"""Streamlit Session State Manager wrapping UI state initialization and operations."""

from __future__ import annotations

import uuid
from typing import Any

import streamlit as st

DEFAULT_SESSION_KEYS: dict[str, Any] = {
    "thread_id": None,
    "dataset_name": "sample_sales.csv",
    "raw_df": None,
    "profile": None,
    "insights": [],
    "charts": [],
    "messages": [],
    "last_result": None,
    "active_filters": [],
    "model_name": "gemini-2.5-flash",
    "temperature": 0.0,
    "max_iterations": 6,
    "tracing_enabled": False,
}


def init_session_state() -> None:
    """Initialize default Streamlit session state keys if not already present."""
    if "thread_id" not in st.session_state or not st.session_state["thread_id"]:
        st.session_state["thread_id"] = f"session_{uuid.uuid4().hex[:10]}"

    for key, default_value in DEFAULT_SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def get_state(key: str, default: Any = None) -> Any:
    """Safely fetch a value from st.session_state.

    Args:
        key: Session state key string.
        default: Default value if key is absent or None.

    Returns:
        Stored session value or default.
    """
    init_session_state()
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Set a key-value pair in st.session_state.

    Args:
        key: Session state key string.
        value: Value object to store.
    """
    init_session_state()
    st.session_state[key] = value


def clear_dataset_session() -> None:
    """Reset dataset profile, insights, charts, and message history."""
    st.session_state["raw_df"] = None
    st.session_state["profile"] = None
    st.session_state["insights"] = []
    st.session_state["charts"] = []
    st.session_state["messages"] = []
    st.session_state["last_result"] = None
    st.session_state["active_filters"] = []
    st.session_state["thread_id"] = f"session_{uuid.uuid4().hex[:10]}"


__all__ = [
    "clear_dataset_session",
    "get_state",
    "init_session_state",
    "set_state",
]
