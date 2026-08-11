"""DeepEval Integration Runner for Stage 8.10 AI Quality Evaluation."""

from __future__ import annotations

import logging
import sys
from typing import Any

from evaluation.config import EvaluationConfig

logger = logging.getLogger(__name__)


def is_deepeval_available() -> bool:
    """Check if deepeval package is installed in environment."""
    try:
        import deepeval  # noqa: F401

        return True
    except ImportError:
        return False


def run_deepeval_suite(config: EvaluationConfig | None = None) -> dict[str, Any]:
    """Run DeepEval AI quality metrics evaluation suite.

    Returns:
        Result summary dictionary.
    """
    cfg = config or EvaluationConfig()

    if not is_deepeval_available():
        print("\n============================================================")
        print("DEEPEVAL INTEGRATION STATUS: OPTIONAL (NOT INSTALLED)")
        print("============================================================")
        print("DeepEval is an optional AI evaluation framework.")
        print("To enable DeepEval metrics (AnswerRelevancy, Faithfulness):")
        print("  pip install deepeval")
        print("============================================================\n")
        return {
            "status": "skipped",
            "reason": "deepeval package not installed",
            "deepeval_available": False,
        }

    try:
        from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
        from deepeval.test_case import LLMTestCase

        # Example DeepEval test case evaluation
        test_case = LLMTestCase(
            input="What is the total revenue?",
            actual_output="Total revenue generated is $756,000.00.",
            retrieval_context=["Total revenue equals 756000.0 across 10 orders."],
        )

        relevancy_metric = AnswerRelevancyMetric(threshold=cfg.thresholds.answer_relevancy)
        faithfulness_metric = FaithfulnessMetric(threshold=cfg.thresholds.faithfulness)

        relevancy_metric.measure(test_case)
        faithfulness_metric.measure(test_case)

        print("\n============================================================")
        print("DEEPEVAL EVALUATION SUITE RESULTS")
        print("============================================================")
        print(
            f"Answer Relevancy Score:  {relevancy_metric.score:.2f} (Passed: {relevancy_metric.is_successful()})"
        )
        print(
            f"Faithfulness Score:      {faithfulness_metric.score:.2f} (Passed: {faithfulness_metric.is_successful()})"
        )
        print("============================================================\n")

        return {
            "status": "completed",
            "deepeval_available": True,
            "answer_relevancy_score": float(relevancy_metric.score),
            "faithfulness_score": float(faithfulness_metric.score),
        }
    except Exception as exc:
        logger.warning("DeepEval execution failed: %s", exc)
        return {
            "status": "failed",
            "error": str(exc),
            "deepeval_available": True,
        }


if __name__ == "__main__":
    res = run_deepeval_suite()
    if res.get("status") == "failed":
        sys.exit(1)
