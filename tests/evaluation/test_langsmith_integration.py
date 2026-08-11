"""Unit tests for LangSmith tracing integration in evaluation runner."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from csv_analytics_agent.graph.runtime import AgentRuntime
from csv_analytics_agent.observability.tracing import configure_langsmith
from evaluation.runner import run_evaluation
from tests.evaluation.runner import EvaluationRunner
from tests.evaluation.schemas import ExpectedBehavior, GoldenTestCase


def test_configure_langsmith_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify configure_langsmith returns False when LANGSMITH_TRACING is false or unset."""
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    assert configure_langsmith() is False


def test_configure_langsmith_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify configure_langsmith handles missing API key gracefully without crashing."""
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    assert configure_langsmith() is False


def test_configure_langsmith_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify configure_langsmith enables tracing when API key is set."""
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "test_mock_key_123")
    monkeypatch.setenv("LANGSMITH_PROJECT", "test-eval-project")
    assert configure_langsmith() is True
    assert os.getenv("LANGSMITH_PROJECT") in ("test-eval-project", "csv-analytics-agent")


def test_offline_mode_evaluation_runs_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify evaluation runner works completely offline when tracing is disabled."""
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)

    ds_file = Path(__file__).parents[2] / "evaluation" / "datasets" / "golden_questions.jsonl"
    report_data = run_evaluation(dataset_path=ds_file, use_mock_llm=True, regression_check=False)

    assert report_data["metadata"]["overall_pass_rate"] == 100.0
    assert report_data["metadata"]["langsmith_enabled"] is False
    assert "evaluation_run_id" in report_data["metadata"]


def test_trace_metadata_and_tags(tmp_path: Path) -> None:
    """Verify metadata and tags are constructed properly and passed to runtime.run."""
    case = GoldenTestCase(
        id="test_001",
        question="What is total revenue?",
        category="analytical",
        expected_behavior=ExpectedBehavior(tool="deterministic", artifact_types=["scalar"]),
    )

    mock_runtime = MagicMock(spec=AgentRuntime)
    mock_runtime.run.return_value = {"messages": [], "analysis_result": None}

    eval_runner = EvaluationRunner(use_mock_llm=False)
    eval_runner.run_case(case, mock_runtime, eval_run_id="2026-08-11_TEST_RUN")

    mock_runtime.run.assert_called_once()
    _, kwargs = mock_runtime.run.call_args

    meta = kwargs.get("metadata", {})
    tags = kwargs.get("tags", [])

    assert meta["evaluation_run_id"] == "2026-08-11_TEST_RUN"
    assert meta["test_case_id"] == "test_001"
    assert meta["question"] == "What is total revenue?"
    assert meta["category"] == "analytical"
    assert meta["prompt_version"] == "v1.0"

    # Verify no raw dataset or secrets in metadata
    assert "dataframe" not in meta
    assert "csv" not in meta
    assert "api_key" not in meta

    assert "evaluation" in tags
    assert "csv-analytics-agent" in tags
    assert "test-case:test_001" in tags
