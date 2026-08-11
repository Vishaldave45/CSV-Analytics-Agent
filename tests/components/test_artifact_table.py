"""Tests for resilient payload parsing in artifact_table component."""

import pytest

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import AnalysisArtifact
from streamlit_app.components.artifact_table import render_table


def test_render_table_handles_mixed_dict_without_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify render_table does not crash on dict payloads that trigger Pandas ValueError."""
    # Dict with mixed types that triggers ambiguous ordering / scalar index issues in pandas
    payload = {"a": {"x": 1}, "b": 2, "c": [1, 2]}
    art = AnalysisArtifact(
        artifact_id="t1",
        artifact_type=PythonArtifactType.TABLE,
        name="test_mixed",
        payload=payload,
    )

    # Mock st functions to prevent Streamlit UI errors during test execution
    import streamlit as st

    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "dataframe", lambda *a, **k: None)
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)

    # Should execute cleanly without raising ValueError
    render_table(art)


def test_render_table_handles_invalid_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify render_table does not crash on ambiguous list payloads."""
    payload = [{"a": 1}, "scalar_string", {"b": 2}]
    art = AnalysisArtifact(
        artifact_id="t2",
        artifact_type=PythonArtifactType.TABLE,
        name="test_list",
        payload=payload,
    )

    import streamlit as st

    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "dataframe", lambda *a, **k: None)
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)

    render_table(art)
