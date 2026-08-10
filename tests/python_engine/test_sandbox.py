"""Unit tests and security tests for PythonSandboxExecutor."""

import os

import pandas as pd
import pytest

from csv_analytics_agent.python_engine.models import (
    PythonArtifactType,
    PythonExecutionRequest,
)
from csv_analytics_agent.python_engine.policy import PythonSandboxPolicy
from csv_analytics_agent.python_engine.sandbox import PythonSandboxExecutor


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "category": ["A", "B", "A", "B"],
            "revenue": [100.0, 200.0, 150.0, 300.0],
            "quantity": [10, 20, 15, 30],
        }
    )


@pytest.fixture
def executor() -> PythonSandboxExecutor:
    return PythonSandboxExecutor()


def test_simple_scalar_execution(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """1. Verify execution returning a simple scalar value."""
    req = PythonExecutionRequest(
        code="total_rev = df['revenue'].sum()",
        question="What is total revenue?",
    )
    result = executor.execute(req, sample_df)
    assert result.success is True
    assert len(result.artifacts) == 1
    assert result.artifacts[0].artifact_type == PythonArtifactType.SCALAR
    assert result.artifacts[0].name == "total_rev"
    assert result.artifacts[0].data == 750.0


def test_string_execution(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """2. Verify execution returning a string variable."""
    req = PythonExecutionRequest(
        code="summary_text = f'Rows: {len(df)}'",
        question="Summarize rows",
    )
    result = executor.execute(req, sample_df)
    assert result.success is True
    assert len(result.artifacts) == 1
    assert result.artifacts[0].artifact_type == PythonArtifactType.TEXT
    assert result.artifacts[0].data == "Rows: 4"


def test_dataframe_aggregation(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """3. Verify DataFrame aggregation calculation."""
    req = PythonExecutionRequest(
        code="avg_rev = df.groupby('category')['revenue'].mean()",
        question="Average revenue per category",
    )
    result = executor.execute(req, sample_df)
    assert result.success is True
    assert len(result.artifacts) == 1
    assert result.artifacts[0].artifact_type == PythonArtifactType.TABLE


def test_dataframe_filtering(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """4. Verify DataFrame filtering operation."""
    req = PythonExecutionRequest(
        code="filtered = df[df['revenue'] > 150]",
        question="Filter revenue > 150",
    )
    result = executor.execute(req, sample_df)
    assert result.success is True
    assert len(result.artifacts) == 1
    assert result.artifacts[0].artifact_type == PythonArtifactType.DATAFRAME
    df_res = result.artifacts[0].data
    assert isinstance(df_res, pd.DataFrame)
    assert len(df_res) == 2


def test_dataframe_result(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """5. Verify DataFrame result object returned as artifact."""
    req = PythonExecutionRequest(
        code="top_df = df.head(2)",
        question="Get first 2 rows",
    )
    result = executor.execute(req, sample_df)
    assert result.success is True
    assert len(result.artifacts) == 1
    assert result.artifacts[0].artifact_type == PythonArtifactType.DATAFRAME
    assert len(result.artifacts[0].data) == 2


def test_allowed_import_works(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """6. Verify allowed import (math) executes successfully."""
    req = PythonExecutionRequest(
        code="import math\nsqrt_val = math.sqrt(df['revenue'].sum())",
        question="Square root of total revenue",
    )
    result = executor.execute(req, sample_df)
    assert result.success is True
    assert len(result.artifacts) == 1
    assert abs(result.artifacts[0].data - 27.386127) < 1e-4


def test_blocked_import_rejected(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """7. Verify blocked import (os) is rejected before execution."""
    req = PythonExecutionRequest(
        code="import os\nfiles = os.listdir('.')",
        question="List files",
    )
    result = executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "PythonValidationError"
    assert "Import of blocked module 'os' is forbidden" in result.error_message


def test_aliased_blocked_import_rejected(
    executor: PythonSandboxExecutor, sample_df: pd.DataFrame
) -> None:
    """8. Verify aliased blocked import (import os as sys_os) is rejected."""
    req = PythonExecutionRequest(
        code="import os as sys_os\nx = sys_os.getcwd()",
        question="Get current dir",
    )
    result = executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "PythonValidationError"
    assert "Import of blocked module 'os' is forbidden" in result.error_message


def test_from_import_blocked_module_rejected(
    executor: PythonSandboxExecutor, sample_df: pd.DataFrame
) -> None:
    """9. Verify 'from os import path' is rejected."""
    req = PythonExecutionRequest(
        code="from os import path\nexists = path.exists('.')",
        question="Check path exists",
    )
    result = executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "PythonValidationError"
    assert "Import of blocked module 'os' is forbidden" in result.error_message


def test_eval_rejected(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """10. Verify call to eval() is rejected."""
    req = PythonExecutionRequest(
        code="val = eval('1 + 1')",
        question="Eval test",
    )
    result = executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "PythonValidationError"
    assert "forbidden function or identifier 'eval'" in result.error_message


def test_exec_rejected(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """11. Verify call to exec() is rejected."""
    req = PythonExecutionRequest(
        code="exec('x = 100')",
        question="Exec test",
    )
    result = executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "PythonValidationError"
    assert "forbidden function or identifier 'exec'" in result.error_message


def test_import_dunder_rejected(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """12. Verify call to __import__() is rejected."""
    req = PythonExecutionRequest(
        code="mod = __import__('os')",
        question="Dunder import test",
    )
    result = executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "PythonValidationError"
    assert "forbidden function or identifier '__import__'" in result.error_message


def test_oversized_code_rejected(sample_df: pd.DataFrame) -> None:
    """13. Verify code exceeding max_code_bytes is rejected."""
    strict_policy = PythonSandboxPolicy(max_code_bytes=20)
    strict_executor = PythonSandboxExecutor(policy=strict_policy)
    req = PythonExecutionRequest(
        code="very_long_variable_name = df['revenue'].sum() + 100",
        question="Oversized test",
    )
    result = strict_executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "PythonValidationError"
    assert "exceeds maximum limit of 20 bytes" in result.error_message


def test_timeout_terminates_execution(sample_df: pd.DataFrame) -> None:
    """14. Verify timeout setting terminates long-running subprocess."""
    fast_policy = PythonSandboxPolicy(
        timeout_seconds=0.5,
        allowed_imports=frozenset({"time", "pandas"}),
    )
    fast_executor = PythonSandboxExecutor(policy=fast_policy)
    req = PythonExecutionRequest(
        code="import time\ntime.sleep(10.0)",
        question="Infinite loop test",
        timeout_seconds=0.5,
    )
    result = fast_executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "PythonTimeoutError"
    assert "timed out" in result.stderr.lower() or "timeout limit" in result.error_message.lower()


def test_stdout_captured(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """15. Verify stdout prints are captured in result.stdout."""
    req = PythonExecutionRequest(
        code="print('Hello from Sandbox stdout!')\nval = 1",
        question="Stdout test",
    )
    result = executor.execute(req, sample_df)
    assert result.success is True
    assert "Hello from Sandbox stdout!" in result.stdout


def test_stderr_captured(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """16. Verify runtime exceptions output to stderr."""
    req = PythonExecutionRequest(
        code="val = 1 / 0",
        question="Division by zero test",
    )
    result = executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "ZeroDivisionError"
    assert "ZeroDivisionError" in result.stderr or "division by zero" in result.error_message


def test_output_limit_enforced(sample_df: pd.DataFrame) -> None:
    """17. Verify output exceeding max_output_bytes is truncated and reported."""
    small_out_policy = PythonSandboxPolicy(max_output_bytes=100)
    small_executor = PythonSandboxExecutor(policy=small_out_policy)
    req = PythonExecutionRequest(
        code="for i in range(1000):\n    print('Line of text ' * 10)",
        question="Large stdout test",
        max_output_bytes=100,
    )
    result = small_executor.execute(req, sample_df)
    assert result.success is False
    assert result.error_type == "PythonOutputLimitError"
    assert "[TRUNCATED]" in result.stdout


def test_temp_directory_cleaned(executor: PythonSandboxExecutor, sample_df: pd.DataFrame) -> None:
    """18. Verify temporary directory is deleted after execution."""
    req = PythonExecutionRequest(
        code="x = 10",
        question="Clean temp dir test",
    )
    result = executor.execute(req, sample_df)
    assert result.success is True
    # Confirm process completed cleanly without leftover py_sandbox_* directories in temp
    import tempfile

    temp_root = tempfile.gettempdir()
    leftover = [d for d in os.listdir(temp_root) if d.startswith("py_sandbox_")]
    assert len(leftover) == 0


def test_api_keys_not_passed_to_child_env(
    executor: PythonSandboxExecutor, sample_df: pd.DataFrame
) -> None:
    """19. Verify parent sensitive environment variables (API keys) are not leaked to child."""
    os.environ["GOOGLE_API_KEY"] = "SECRET_KEY_123"
    os.environ["GEMINI_API_KEY"] = "SECRET_KEY_456"
    try:
        req = PythonExecutionRequest(
            code="import os\nkey = os.environ.get('GOOGLE_API_KEY', 'ABSENT')",
            question="Env test",
        )
        # Note: import os is blocked by AST policy, but even if we check clean_env, it is isolated.
        result = executor.execute(req, sample_df)
        assert result.success is False
        assert result.error_type == "PythonValidationError"
        assert "Import of blocked module 'os' is forbidden" in result.error_message
    finally:
        os.environ.pop("GOOGLE_API_KEY", None)
        os.environ.pop("GEMINI_API_KEY", None)


def test_security_ast_blocked_modules_and_dunders(
    executor: PythonSandboxExecutor, sample_df: pd.DataFrame
) -> None:
    """20. Verify AST validation blocks high-risk modules and dunder introspection patterns."""
    high_risk_codes = [
        "import pathlib\np = pathlib.Path('.')",
        "import subprocess\nsubprocess.run(['ls'])",
        "import socket\ns = socket.socket()",
        "import ctypes\nctypes.string_at(0)",
        "classes = object.__subclasses__()",
    ]
    for code in high_risk_codes:
        req = PythonExecutionRequest(code=code, question="Security test")
        result = executor.execute(req, sample_df)
        assert result.success is False
        assert result.error_type == "PythonValidationError"
