"""Unit tests for LangSmith tracing configuration and metadata."""

from __future__ import annotations

import os
from unittest import mock

from csv_analytics_agent.observability.config import ObservabilitySettings
from csv_analytics_agent.observability.tracing import (
    configure_langsmith,
    get_traced_metadata,
)


def _make_settings(**kwargs: object) -> ObservabilitySettings:
    """Create ObservabilitySettings with explicit constructor args to bypass .env file."""
    defaults = dict(
        tracing_v2=False,
        api_key=None,
        project="csv-analytics-agent",
        endpoint="https://api.smith.langchain.com",
        session="development",
        tags_raw="local,csv-agent",
    )
    defaults.update(kwargs)
    return ObservabilitySettings(**defaults)  # type: ignore[arg-type]


def test_configure_langsmith_disabled_by_default() -> None:
    """Verify configure_langsmith returns False when tracing_v2 is False."""
    settings = _make_settings(tracing_v2=False)
    enabled = configure_langsmith(settings)
    assert enabled is False


def test_configure_langsmith_missing_api_key() -> None:
    """Verify graceful fallback when tracing is enabled but API key is missing."""
    settings = _make_settings(tracing_v2=True, api_key=None)
    enabled = configure_langsmith(settings)
    assert enabled is False


def test_configure_langsmith_success() -> None:
    """Verify configure_langsmith succeeds when API key and tracing_v2 are set."""
    settings = _make_settings(tracing_v2=True, api_key="test_api_key_123", project="test-project")
    with mock.patch.dict(os.environ, {}, clear=False):
        enabled = configure_langsmith(settings)
        # Assert inside the context so env changes set by configure_langsmith are visible
        assert enabled is True
        assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
        assert os.environ.get("LANGCHAIN_PROJECT") == "test-project"



def test_get_traced_metadata() -> None:
    """Verify get_traced_metadata payload structure."""
    meta = get_traced_metadata(
        thread_id="t_meta_123",
        dataset_name="sales.csv",
        model_name="gemini-2.5-flash",
    )
    assert meta["thread_id"] == "t_meta_123"
    assert meta["dataset_name"] == "sales.csv"
    assert meta["model_name"] == "gemini-2.5-flash"
    assert "agent_version" in meta
