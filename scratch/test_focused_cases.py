import logging
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from csv_analytics_agent.evaluation.runner import EvaluationRunner


def main():
    runner = EvaluationRunner(use_mock_llm=False)
    cases = runner.load_cases()
    focused_ids = {"001", "004", "017", "018", "019"}
    target_cases = [c for c in cases if c.id in focused_ids]

    db_path = Path("/tmp/eval_test.db")
    runtime = runner.create_runtime(db_path)

    print("\n--- FOCUSED LIVE EVALUATION (001, 004, 017, 018, 019) ---")
    for idx, case in enumerate(target_cases):
        if idx > 0:
            time.sleep(4.0)
        res = runner.run_case(case, runtime)
        print(f"\nCase {case.id}: {case.question}")
        print(f"  Artifact Passed: {res.artifact_passed}")
        print(f"  Tool Passed:     {res.tool_passed}")
        print(f"  Actual Tools:    {res.actual_tools}")
        print(f"  Actual Artifacts:{res.actual_artifacts}")
        print(f"  Expected Arts:   {case.expected_behavior.artifact_types}")
        print(f"  Failures:        {res.failures}")


if __name__ == "__main__":
    main()
