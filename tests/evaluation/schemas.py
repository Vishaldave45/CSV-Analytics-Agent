"""Evaluation domain schemas for Stage 8.9 Golden Dataset & Evaluation System."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ToolClass = Literal["deterministic", "python", "either", "none"]
ArtifactTypeLiteral = Literal[
    "text",
    "scalar",
    "table",
    "dataframe",
    "interactive",
    "image",
    "diagram",
    "file",
    "none",
]


@dataclass
class ExpectedBehavior:
    """Expected behavioral criteria for a golden test case."""

    tool: ToolClass = "either"
    artifact_types: list[str] = field(default_factory=lambda: ["text"])
    requires_python: bool = False
    expected_numeric_values: dict[str, float] = field(default_factory=dict)
    numeric_tolerance: float = 1e-3
    security_expectation: Literal["safe", "reject"] = "safe"
    expected_grounding_facts: dict[str, Any] = field(default_factory=dict)


@dataclass
class GoldenTestCase:
    """Representation of a single or multi-turn golden evaluation case."""

    id: str
    question: str | list[str]
    category: str
    expected_behavior: ExpectedBehavior

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GoldenTestCase:
        """Construct GoldenTestCase instance from raw dictionary."""
        eb_dict = data.get("expected_behavior", {})
        eb = ExpectedBehavior(
            tool=eb_dict.get("tool", "either"),
            artifact_types=eb_dict.get("artifact_types", ["text"]),
            requires_python=eb_dict.get("requires_python", False),
            expected_numeric_values=eb_dict.get("expected_numeric_values", {}),
            numeric_tolerance=eb_dict.get("numeric_tolerance", 1e-3),
            security_expectation=eb_dict.get("security_expectation", "safe"),
            expected_grounding_facts=eb_dict.get("expected_grounding_facts", {}),
        )
        return cls(
            id=data["id"],
            question=data["question"],
            category=data["category"],
            expected_behavior=eb,
        )


@dataclass
class EvaluationResult:
    """Individual test case evaluation output."""

    case_id: str
    question: str | list[str]
    category: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    actual_tools: list[str] = field(default_factory=list)
    expected_tools: str = "either"
    actual_artifacts: list[str] = field(default_factory=list)
    expected_artifacts: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    grounding_passed: bool = True
    security_passed: bool = True


@dataclass
class EvaluationSummary:
    """Aggregated evaluation metric summary across golden test cases."""

    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    overall_pass_rate: float = 0.0
    tool_selection_accuracy: float = 0.0
    artifact_type_accuracy: float = 0.0
    deterministic_case_pass_rate: float = 0.0
    python_case_pass_rate: float = 0.0
    security_pass_rate: float = 0.0
    follow_up_pass_rate: float = 0.0
    category_pass_rates: dict[str, float] = field(default_factory=dict)
