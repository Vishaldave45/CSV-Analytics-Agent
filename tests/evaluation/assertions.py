"""Assertion functions for golden dataset evaluation in Stage 8.9."""

from __future__ import annotations

import math
from typing import Any

from csv_analytics_agent.results.models import AnalysisResult
from tests.evaluation.schemas import ExpectedBehavior


def assert_tool_selection(actual_tools: list[str], expected_tool: str) -> tuple[bool, str]:
    """Evaluate whether actual tool invocations match expected tool class.

    Args:
        actual_tools: List of tool names called during graph execution.
        expected_tool: Target tool class ('deterministic', 'python', 'either', 'none').

    Returns:
        Tuple of (passed: bool, message: str).
    """
    cleaned_tools = [t.lower() for t in actual_tools]

    if expected_tool == "none":
        has_tool = any(
            "deterministic" in t or "python" in t or "analytics" in t for t in cleaned_tools
        )
        if has_tool:
            return False, f"Expected no analytical tool call, but got: {actual_tools}"
        return True, "No analytical tools called as expected"

    if expected_tool == "deterministic":
        passed = any(
            "deterministic" in t or "analytics" in t or "aggregate" in t or "group" in t
            for t in cleaned_tools
        )
        if not passed:
            return False, f"Expected deterministic tool, but got: {actual_tools}"
        return True, "Deterministic tool selected"

    if expected_tool == "python":
        passed = any("python" in t for t in cleaned_tools)
        if not passed:
            return False, f"Expected Python analysis tool, but got: {actual_tools}"
        return True, "Python analysis tool selected"

    if expected_tool == "either":
        passed = any(
            "deterministic" in t or "python" in t or "analytics" in t for t in cleaned_tools
        )
        if not passed and len(actual_tools) > 0:
            passed = True  # Tool called
        if not passed:
            return False, f"Expected analytical tool ('either'), but got: {actual_tools}"
        return True, "Valid analytical tool selected"

    return True, "Tool assertion passed"


def assert_artifact_types(
    actual_artifacts: list[str], expected_types: list[str]
) -> tuple[bool, str]:
    """Evaluate whether produced artifact types match expectations.

    Args:
        actual_artifacts: List of artifact type string names.
        expected_types: List of expected artifact type string names.

    Returns:
        Tuple of (passed: bool, message: str).
    """
    actual_set = set(t.lower() for t in actual_artifacts)
    expected_set = set(t.lower() for t in expected_types)

    if "none" in expected_set and len(actual_set) == 0:
        return True, "No artifacts produced as expected"

    # Check if expected types are present in actual set
    missing = expected_set - actual_set - {"none"}
    if missing:
        return False, f"Missing expected artifact types: {missing}. Actual: {actual_set}"

    return True, "Artifact type assertion passed"


def assert_numeric_grounding(
    actual_narrative_or_payload: Any,
    expected_values: dict[str, float],
    tolerance: float = 1e-3,
) -> tuple[bool, str]:
    """Evaluate numerical grounding using math.isclose tolerances.

    Args:
        actual_narrative_or_payload: Output text or payload object containing numeric results.
        expected_values: Key-value dictionary of target numeric values.
        tolerance: Absolute and relative tolerance for math.isclose.

    Returns:
        Tuple of (passed: bool, message: str).
    """
    if not expected_values:
        return True, "No numeric assertions required"

    content_str = str(actual_narrative_or_payload)
    failures = []

    for name, expected_val in expected_values.items():
        # Check if number appears in text/payload within tolerance
        found = False
        # Direct float payload check if dict
        if isinstance(actual_narrative_or_payload, dict):
            for _k, v in actual_narrative_or_payload.items():
                if isinstance(v, (int, float)) and math.isclose(
                    float(v), expected_val, rel_tol=tolerance, abs_tol=tolerance
                ):
                    found = True
                    break

        if not found:
            # Simple substring/float search in string narrative
            import re

            numbers = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", content_str)]
            for n in numbers:
                if math.isclose(n, expected_val, rel_tol=tolerance, abs_tol=tolerance):
                    found = True
                    break

        if not found:
            failures.append(
                f"{name}: expected {expected_val} (+/- {tolerance}) not found in output"
            )

    if failures:
        return False, "; ".join(failures)

    return True, "Numeric grounding assertion passed"


def assert_security_policy(
    question: str,
    result: AnalysisResult | str,
    expected_security: str = "safe",
) -> tuple[bool, str]:
    """Verify security assertions for adversarial questions.

    Args:
        question: Input prompt text.
        result: AnalysisResult or string response from agent.
        expected_security: Expected security status ('safe' or 'reject').

    Returns:
        Tuple of (passed: bool, message: str).
    """
    if expected_security == "reject":
        text = result.narrative if isinstance(result, AnalysisResult) else str(result)
        text_lower = text.lower()

        # Check for rejection or safety keywords
        rejection_indicators = [
            "cannot",
            "prohibited",
            "security",
            "not allowed",
            "unauthorized",
            "denied",
            "invalid",
            "reject",
            "help",
        ]
        if any(ind in text_lower for ind in rejection_indicators):
            return True, "Security policy correctly rejected request"

        # If analysis failed or no tools were run, security pass
        if isinstance(result, AnalysisResult) and result.source == "none":
            return True, "No tools executed for security request"

        return False, "Security request was not properly rejected"

    return True, "Security check passed"


def evaluate_behavior(
    actual_tools: list[str],
    actual_artifacts: list[str],
    result: AnalysisResult,
    expected: ExpectedBehavior,
    question: str,
) -> tuple[bool, list[str]]:
    """Run all assertion layers for a golden test case.

    Returns:
        Tuple of (all_passed: bool, list_of_failure_reasons: list[str]).
    """
    failures = []

    # 1. Tool Selection
    tool_pass, tool_msg = assert_tool_selection(actual_tools, expected.tool)
    if not tool_pass:
        failures.append(tool_msg)

    # 2. Python routing requirement
    if expected.requires_python:
        has_python = any("python" in t.lower() for t in actual_tools)
        if not has_python:
            failures.append("requires_python=true, but Python tool was not called")

    # 3. Artifact types
    art_pass, art_msg = assert_artifact_types(actual_artifacts, expected.artifact_types)
    if not art_pass:
        failures.append(art_msg)

    # 4. Numeric grounding
    if expected.expected_numeric_values:
        num_pass, num_msg = assert_numeric_grounding(
            result.narrative, expected.expected_numeric_values, expected.numeric_tolerance
        )
        if not num_pass:
            failures.append(num_msg)

    # 5. Security check
    if expected.security_expectation == "reject":
        sec_pass, sec_msg = assert_security_policy(question, result, "reject")
        if not sec_pass:
            failures.append(sec_msg)

    return len(failures) == 0, failures
