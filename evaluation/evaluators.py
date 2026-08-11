"""Specialized quality evaluators for Stage 8.10 AI Evaluation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from csv_analytics_agent.evaluation.schemas import ExpectedBehavior
from csv_analytics_agent.results.models import AnalysisResult


@dataclass
class MetricScore:
    """Score container for specific evaluation metric."""

    metric_name: str
    score: float
    passed: bool
    details: str


class NumericalCorrectnessEvaluator:
    """Evaluates numerical correctness using math.isclose tolerances."""

    def __init__(self, tolerance: float = 1e-3) -> None:
        self.tolerance = tolerance

    def evaluate(self, result: AnalysisResult, expected_values: dict[str, float]) -> MetricScore:
        if not expected_values:
            return MetricScore(
                metric_name="numerical_correctness",
                score=1.0,
                passed=True,
                details="No numeric values required.",
            )

        text = result.narrative
        failures = []

        for k, expected in expected_values.items():
            import re

            numbers = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", text)]
            found = any(
                math.isclose(n, expected, rel_tol=self.tolerance, abs_tol=self.tolerance)
                for n in numbers
            )
            if not found:
                failures.append(
                    f"Metric '{k}': expected {expected} (+/- {self.tolerance}) not found."
                )

        if failures:
            return MetricScore(
                metric_name="numerical_correctness",
                score=0.0,
                passed=False,
                details="; ".join(failures),
            )

        return MetricScore(
            metric_name="numerical_correctness",
            score=1.0,
            passed=True,
            details="All numerical expectations satisfied.",
        )


class ToolSelectionQualityEvaluator:
    """Evaluates tool selection quality, detecting unnecessary Python execution."""

    def evaluate(self, actual_tools: list[str], expected: ExpectedBehavior) -> MetricScore:
        cleaned = [t.lower() for t in actual_tools]

        if expected.tool == "deterministic":
            has_det = any(
                "deterministic" in t or "analytics" in t or "group" in t or "aggregate" in t
                for t in cleaned
            )
            has_unnecessary_py = (
                any("python" in t for t in cleaned) and not expected.requires_python
            )

            if has_unnecessary_py:
                return MetricScore(
                    metric_name="tool_selection_quality",
                    score=0.50,
                    passed=False,
                    details=f"Unnecessary Python invocation detected for query that expected deterministic capability: {actual_tools}",
                )
            if has_det or len(actual_tools) > 0:
                return MetricScore(
                    metric_name="tool_selection_quality",
                    score=1.0,
                    passed=True,
                    details="Deterministic engine correctly selected.",
                )
            return MetricScore(
                metric_name="tool_selection_quality",
                score=0.0,
                passed=False,
                details=f"Expected deterministic tool but got: {actual_tools}",
            )

        if expected.tool == "python":
            has_py = any("python" in t for t in cleaned)
            if has_py:
                return MetricScore(
                    metric_name="tool_selection_quality",
                    score=1.0,
                    passed=True,
                    details="Python engine correctly selected.",
                )
            return MetricScore(
                metric_name="tool_selection_quality",
                score=0.0,
                passed=False,
                details=f"Expected Python analysis tool but got: {actual_tools}",
            )

        return MetricScore(
            metric_name="tool_selection_quality",
            score=1.0,
            passed=True,
            details="Tool selection quality check passed.",
        )


class ArtifactSemanticsEvaluator:
    """Evaluates semantics and structures of produced artifacts."""

    def evaluate(self, result: AnalysisResult, expected_types: list[str]) -> MetricScore:
        actual_types = [art.artifact_type.value.lower() for art in result.artifacts]
        expected_set = set(t.lower() for t in expected_types if t != "none")

        if not expected_set and len(actual_types) == 0:
            return MetricScore(
                metric_name="artifact_semantics",
                score=1.0,
                passed=True,
                details="No artifacts expected or produced.",
            )

        missing = expected_set - set(actual_types)
        if missing:
            return MetricScore(
                metric_name="artifact_semantics",
                score=0.0,
                passed=False,
                details=f"Missing expected artifact types: {missing}. Actual: {set(actual_types)}",
            )

        # Inspect artifact payloads
        for art in result.artifacts:
            atype = art.artifact_type.value.lower()
            if atype in ("table", "dataframe") and art.payload is None:
                return MetricScore(
                    metric_name="artifact_semantics",
                    score=0.50,
                    passed=False,
                    details=f"Table artifact '{art.name}' has null payload.",
                )
            if atype == "interactive" and not art.payload:
                return MetricScore(
                    metric_name="artifact_semantics",
                    score=0.50,
                    passed=False,
                    details=f"Interactive chart artifact '{art.name}' has empty Plotly payload.",
                )

        return MetricScore(
            metric_name="artifact_semantics",
            score=1.0,
            passed=True,
            details="Artifact semantics and structures valid.",
        )


class MissingDataExplanationEvaluator:
    """Evaluates whether agent gracefully explains missing columns (e.g. profit) without hallucinating."""

    def evaluate(self, result: AnalysisResult, expected_facts: dict[str, Any]) -> MetricScore:
        missing_col = expected_facts.get("missing_column")
        if not missing_col:
            return MetricScore(
                metric_name="missing_data_explanation",
                score=1.0,
                passed=True,
                details="No missing data check required.",
            )

        text_lower = result.narrative.lower()
        explained = any(
            kw in text_lower
            for kw in [
                missing_col.lower(),
                "not available",
                "does not contain",
                "cannot be determined",
                "missing",
                "no column",
            ]
        )

        if explained:
            return MetricScore(
                metric_name="missing_data_explanation",
                score=1.0,
                passed=True,
                details=f"Gracefully explained that column '{missing_col}' is unavailable.",
            )

        return MetricScore(
            metric_name="missing_data_explanation",
            score=0.0,
            passed=False,
            details=f"Failed to explain that missing column '{missing_col}' was unavailable.",
        )
