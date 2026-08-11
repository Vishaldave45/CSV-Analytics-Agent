"""Custom Python provider interfacing Promptfoo with CSV Analytics Agent AgentRuntime."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from csv_analytics_agent.evaluation.runner import EvaluationRunner
from csv_analytics_agent.evaluation.schemas import ExpectedBehavior, GoldenTestCase
from csv_analytics_agent.results.models import AnalysisResult
from evaluation.judge import sanitize_payload


def call_api(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Promptfoo custom provider entrypoint.

    Args:
        prompt: Prompt template string passed by Promptfoo.
        options: Provider options dictionary.
        context: Execution context containing variables (`vars`).

    Returns:
        Promptfoo output response dictionary.
    """
    vars_dict = context.get("vars", {})
    question = vars_dict.get("question", "What is the dataset summary?")
    use_mock = vars_dict.get("use_mock", True)

    ds_file = Path(__file__).parents[2] / "evaluation" / "datasets" / "golden_questions.jsonl"
    eval_runner = EvaluationRunner(dataset_path=ds_file, use_mock_llm=use_mock)

    case = GoldenTestCase(
        id="promptfoo_eval_case",
        question=question,
        category=vars_dict.get("category", "analytical"),
        expected_behavior=ExpectedBehavior(
            tool=vars_dict.get("expected_tool", "either"),
            security_expectation=vars_dict.get("security_expectation", "safe"),
        ),
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "promptfoo_eval.db"
        runtime = eval_runner.create_runtime(db_path)
        eval_res = eval_runner.run_case(case, runtime, eval_run_id="promptfoo_run")

        real_res = getattr(eval_res, "actual_result", None)
        narrative = (
            real_res.narrative
            if isinstance(real_res, AnalysisResult)
            else "Processed question successfully."
        )

        output_text = f"Output: {narrative}\nTools Used: {', '.join(eval_res.actual_tools)}\nSecurity Passed: {eval_res.security_passed}"

        return {
            "output": output_text,
            "metadata": {
                "question": sanitize_payload(question),
                "actual_tools": eval_res.actual_tools,
                "passed": eval_res.passed,
                "security_passed": eval_res.security_passed,
                "narrative": narrative,
            },
        }
