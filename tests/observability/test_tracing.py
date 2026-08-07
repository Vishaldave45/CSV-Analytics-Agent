"""Unit tests for LangSmith tracing configuration and metadata."""

import os

from csv_analytics_agent.observability.config import ObservabilitySettings
from csv_analytics_agent.observability.tracing import (
    configure_langsmith,
    get_traced_metadata,
)


def test_configure_langsmith_disabled_by_default() -> None:
    """Verify configure_langsmith returns False when tracing_v2 is False."""
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    settings = ObservabilitySettings(tracing_v2=False)
    enabled = configure_langsmith(settings)
    assert enabled is False


def test_configure_langsmith_missing_api_key() -> None:
    """Verify graceful fallback when tracing is enabled but API key is missing."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.pop("LANGCHAIN_API_KEY", None)
    settings = ObservabilitySettings(tracing_v2=True, api_key=None)

    enabled = configure_langsmith(settings)
    assert enabled is False


def test_configure_langsmith_success() -> None:
    """Verify configure_langsmith succeeds when API key and tracing_v2 are set."""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = "test_api_key_123"
    os.environ["LANGCHAIN_PROJECT"] = "test-project"

    settings = ObservabilitySettings(
        tracing_v2=True,
        api_key="test_api_key_123",
        project="test-project",
    )
    enabled = configure_langsmith(settings)
    assert enabled is True
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
    assert os.environ.get("LANGCHAIN_PROJECT") == "test-project"


def test_get_traced_metadata() -> None:
    """Verify get_traced_metadata payload structure."""
    meta = get_traced_metadata(
        thread_id="t_meta_123",
        dataset_name="sales.csv",
        model_name="gemini-1.5-flash",
    )
    assert meta["thread_id"] == "t_meta_123"
    assert meta["dataset_name"] == "sales.csv"
    assert meta["model_name"] == "gemini-1.5-flash"
    assert "agent_version" in meta
