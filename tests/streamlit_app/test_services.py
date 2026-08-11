"""Unit tests for Streamlit App Services Layer."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from csv_analytics_agent.llm.gemini import DEFAULT_MODEL_NAME
from streamlit_app.services.backend import (
    build_configured_registry,
    create_agent_runtime,
    get_insights,
    recommend_visualization,
    render_chart_image,
    upload_dataset,
)
from streamlit_app.services.session import (
    clear_dataset_session,
    consume_pending_prompt,
    get_state,
    init_session_state,
    set_state,
)


@pytest.fixture
def sample_csv_bytes() -> bytes:
    return b"Date,Product,Revenue\n2024-01-01,Gadget,100.0\n2024-01-02,Widget,200.0\n"


def test_session_service_operations() -> None:
    """Verify session state initialization and mutation helpers."""
    init_session_state()
    assert get_state("model_name") == DEFAULT_MODEL_NAME

    set_state("custom_key", "custom_val")
    assert get_state("custom_key") == "custom_val"

    clear_dataset_session()
    assert get_state("raw_df") is None
    assert get_state("insights") == []


def test_consume_pending_prompt_prefers_direct_input() -> None:
    """Verify chat input overrides pending prompt and clears the pending value."""
    init_session_state()
    set_state("pending_prompt", "suggested query")

    result = consume_pending_prompt("my explicit query")
    assert result == "my explicit query"
    assert get_state("pending_prompt") is None


def test_consume_pending_prompt_uses_pending_prompt_when_no_input() -> None:
    """Verify pending prompt is consumed only when no direct chat input exists."""
    init_session_state()
    set_state("pending_prompt", "suggested query")

    result = consume_pending_prompt(None)
    assert result == "suggested query"
    assert get_state("pending_prompt") is None


def test_backend_loader_and_profiler(sample_csv_bytes: bytes) -> None:
    """Verify upload_dataset backend function."""
    df, profile, content_hash = upload_dataset(sample_csv_bytes, filename="test.csv")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "Product" in df.columns
    assert len(content_hash) == 64
    assert profile.summary.row_count == 2
    assert profile.summary.column_count == 3


def test_backend_insights_and_visualization(sample_csv_bytes: bytes) -> None:
    """Verify get_insights and recommend_visualization backend functions."""
    df, profile, _ = upload_dataset(sample_csv_bytes, filename="test.csv")

    insights = get_insights(profile)
    assert isinstance(insights, list)

    charts = recommend_visualization(profile, insights=insights)
    assert isinstance(charts, list)
    assert len(charts) > 0

    img_bytes = render_chart_image(charts[0], df)
    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 0


@patch("streamlit_app.services.backend.MemoryService")
def test_backend_build_registry_and_runtime(
    mock_memory_cls: MagicMock, sample_csv_bytes: bytes
) -> None:
    """Verify build_configured_registry and create_agent_runtime backend functions."""
    mock_memory_cls.return_value = MagicMock()
    df, _, _ = upload_dataset(sample_csv_bytes, filename="test.csv")
    registry = build_configured_registry()
    assert len(registry.discover()) > 0

    runtime = create_agent_runtime(df)
    assert runtime is not None
