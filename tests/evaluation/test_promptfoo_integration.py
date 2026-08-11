"""Unit tests for Promptfoo integration and runner module."""

from __future__ import annotations

from pathlib import Path

from evaluation.promptfoo_runner import is_promptfoo_installed, run_promptfoo_suite


def test_is_promptfoo_installed_check() -> None:
    """Verify is_promptfoo_installed returns boolean without error."""
    installed = is_promptfoo_installed()
    assert isinstance(installed, bool)


def test_promptfoo_config_files_exist() -> None:
    """Verify promptfooconfig.yaml and prompt test suites exist."""
    promptfoo_dir = Path(__file__).parents[2] / "evaluation" / "promptfoo"
    config_yaml = promptfoo_dir / "promptfooconfig.yaml"
    tests_dir = promptfoo_dir / "tests"

    assert config_yaml.exists()
    assert (tests_dir / "router_tests.yaml").exists()
    assert (tests_dir / "planner_tests.yaml").exists()
    assert (tests_dir / "response_tests.yaml").exists()
    assert (tests_dir / "python_security_tests.yaml").exists()
    assert (tests_dir / "adversarial_tests.yaml").exists()
    assert (tests_dir / "followup_tests.yaml").exists()


def test_run_promptfoo_suite_execution() -> None:
    """Verify run_promptfoo_suite executes cleanly and outputs valid summary."""
    result = run_promptfoo_suite()

    assert result["status"] == "completed"
    assert "passed" in result
    assert "failed" in result
    assert "pass_rate" in result
    assert "evaluation_run_id" in result
    assert result["pass_rate"] >= 0.0
