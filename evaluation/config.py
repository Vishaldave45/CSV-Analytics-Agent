"""Configuration & thresholds for Stage 8.10 AI Quality & LLM Evaluation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvaluationThresholds:
    """Configurable quality score thresholds for AI evaluations."""

    answer_relevancy: float = 0.80
    faithfulness: float = 0.80
    correctness: float = 0.85
    tool_selection: float = 0.90
    artifact_accuracy: float = 0.90
    security_pass_rate: float = 1.00


@dataclass
class EvaluationConfig:
    """Master configuration settings for Stage 8.10 evaluation execution."""

    dataset_version: str = "1.0"
    eval_model: str = field(default_factory=lambda: os.getenv("EVAL_MODEL", "gemini-2.5-flash"))
    judge_model: str = field(
        default_factory=lambda: os.getenv("EVAL_JUDGE_MODEL", "gemini-2.5-flash")
    )
    thresholds: EvaluationThresholds = field(default_factory=EvaluationThresholds)

    base_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    reports_dir: Path = field(default_factory=lambda: Path(__file__).parent / "reports")
    dataset_path: Path = field(
        default_factory=lambda: (
            Path(__file__).parents[1]
            / "tests"
            / "evaluation"
            / "datasets"
            / "golden_questions.json"
        )
    )

    def __post_init__(self) -> None:
        """Ensure directories exist."""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
