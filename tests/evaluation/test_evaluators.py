"""Unit tests for Stage 8.10 Evaluation Engine & Evaluators."""

from __future__ import annotations

from tests.evaluation.schemas import ExpectedBehavior

from csv_analytics_agent.python_engine.models import PythonArtifactType
from csv_analytics_agent.results.models import AnalysisArtifact, AnalysisResult, AnalysisStatus
from evaluation.evaluators import (
    ArtifactSemanticsEvaluator,
    MissingDataExplanationEvaluator,
    NumericalCorrectnessEvaluator,
    ToolSelectionQualityEvaluator,
)
from evaluation.judge import StructuredLLMJudge, sanitize_payload


def test_sanitize_payload() -> None:
    """Verify secrets and API keys are redacted from evaluation payloads."""
    secret_text = (
        "Key: AIzaSy123456789012345678901234567890123 and lsv2_pt_12345678901234567890123456789012"
    )
    sanitized = sanitize_payload(secret_text)
    assert "AIzaSy" not in sanitized
    assert "lsv2_pt_" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized


def test_numerical_correctness_evaluator_pass() -> None:
    """Verify numerical evaluator passes when numbers match within tolerance."""
    evaluator = NumericalCorrectnessEvaluator(tolerance=1e-3)
    res = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Total revenue is 756000.0 and average is 124.5.",
    )
    score = evaluator.evaluate(res, {"total_revenue": 756000.0, "mean": 124.5})
    assert score.passed
    assert score.score == 1.0


def test_numerical_correctness_evaluator_fail() -> None:
    """Verify numerical evaluator fails when numbers differ beyond tolerance."""
    evaluator = NumericalCorrectnessEvaluator(tolerance=1e-3)
    res = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Total revenue is 500000.0.",
    )
    score = evaluator.evaluate(res, {"total_revenue": 756000.0})
    assert not score.passed
    assert score.score == 0.0


def test_tool_selection_quality_unnecessary_python_fail() -> None:
    """Verify unnecessary Python invocation for deterministic query is penalized."""
    evaluator = ToolSelectionQualityEvaluator()
    eb = ExpectedBehavior(tool="deterministic", requires_python=False)

    # Actual tools includes python_analysis unnecessarily
    score = evaluator.evaluate(["deterministic_engine", "python_analysis"], eb)
    assert not score.passed
    assert score.score == 0.50
    assert "Unnecessary Python invocation" in score.details


def test_tool_selection_quality_python_required_pass() -> None:
    """Verify Python tool selection passes when required."""
    evaluator = ToolSelectionQualityEvaluator()
    eb = ExpectedBehavior(tool="python", requires_python=True)

    score = evaluator.evaluate(["python_analysis"], eb)
    assert score.passed
    assert score.score == 1.0


def test_artifact_semantics_evaluator() -> None:
    """Verify artifact semantics evaluator checks expected artifact types and payloads."""
    evaluator = ArtifactSemanticsEvaluator()
    tbl_art = AnalysisArtifact(
        artifact_type=PythonArtifactType.TABLE,
        name="test_table",
        payload={"cols": ["a"]},
    )
    res = AnalysisResult(status=AnalysisStatus.SUCCESS, artifacts=[tbl_art])

    # Expecting table
    score_pass = evaluator.evaluate(res, ["table"])
    assert score_pass.passed

    # Expecting interactive chart which is missing
    score_fail = evaluator.evaluate(res, ["table", "interactive"])
    assert not score_fail.passed
    assert "Missing expected artifact types" in score_fail.details


def test_missing_data_explanation_evaluator() -> None:
    """Verify missing data explanation evaluator detects graceful explanations."""
    evaluator = MissingDataExplanationEvaluator()

    # Pass case: explains column is missing
    res_explained = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Net profit cannot be determined because column 'profit' is missing from the dataset.",
    )
    score_pass = evaluator.evaluate(res_explained, {"missing_column": "profit"})
    assert score_pass.passed

    # Fail case: fails to explain missing column
    res_unexplained = AnalysisResult(
        status=AnalysisStatus.SUCCESS,
        narrative="Electronics is the top category.",
    )
    score_fail = evaluator.evaluate(res_unexplained, {"missing_column": "profit"})
    assert not score_fail.passed


def test_structured_llm_judge_fallback() -> None:
    """Verify StructuredLLMJudge returns valid fallback when live LLM is None."""
    judge = StructuredLLMJudge(llm=None)
    res = judge.evaluate_relevancy("What is total revenue?", "Total revenue is $756,000.")
    assert res.passed
    assert res.score == 1.0
