"""Unit tests for Streamlit App Services Layer."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from streamlit_app.services.backend import (
    build_configured_registry,
    create_agent_runtime,
    generate_insights_for_dataset,
    load_dataset_from_bytes,
    recommend_visualizations_for_dataset,
    render_chart_image,
)
from streamlit_app.services.session import (
    clear_dataset_session,
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
    assert get_state("model_name") == "gemini-2.0-flash"

    set_state("custom_key", "custom_val")
    assert get_state("custom_key") == "custom_val"

    clear_dataset_session()
    assert get_state("raw_df") is None
    assert get_state("insights") == []


def test_backend_loader_and_profiler(sample_csv_bytes: bytes) -> None:
    """Verify load_dataset_from_bytes and profile_dataset backend functions."""
    df, profile, content_hash = load_dataset_from_bytes(sample_csv_bytes, filename="test.csv")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "Product" in df.columns
    assert len(content_hash) == 64
    assert profile.summary.row_count == 2
    assert profile.summary.column_count == 3


def test_backend_insights_and_visualization(sample_csv_bytes: bytes) -> None:
    """Verify generate_insights and recommend_visualizations backend functions."""
    df, profile, _ = load_dataset_from_bytes(sample_csv_bytes, filename="test.csv")

    insights = generate_insights_for_dataset(profile)
    assert isinstance(insights, list)

    charts = recommend_visualizations_for_dataset(profile, insights=insights)
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
    df, _, _ = load_dataset_from_bytes(sample_csv_bytes, filename="test.csv")
    registry = build_configured_registry()
    assert len(registry.discover()) > 0

    runtime = create_agent_runtime(df)
    assert runtime is not None
