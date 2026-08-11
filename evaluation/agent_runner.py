"""Full Agent Runtime Evaluation Runner for CSV Analytics Agent.

Workflow:
  uv run python -m evaluation.agent_runner [--live-llm]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation.runner import run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Full CSV Agent Runtime Evaluation")
    parser.add_argument(
        "--live-llm", action="store_true", help="Execute evaluation using live Gemini LLM API"
    )
    args = parser.parse_args()

    ds_path = Path(__file__).parent / "datasets" / "golden_questions.jsonl"
    run_evaluation(dataset_path=ds_path, use_mock_llm=not args.live_llm, regression_check=False)


if __name__ == "__main__":
    main()
