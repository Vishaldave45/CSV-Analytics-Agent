"""Unit tests for PythonSandboxPolicy and AST validation."""

import pytest
from pydantic import ValidationError

from csv_analytics_agent.python_engine.errors import PythonValidationError
from csv_analytics_agent.python_engine.policy import (
    DEFAULT_BLOCKED_IMPORTS,
    PythonSandboxPolicy,
    validate_python_code,
)


def test_default_policy_valid() -> None:
    """Verify default PythonSandboxPolicy initialization and values."""
    policy = PythonSandboxPolicy()
    assert policy.timeout_seconds == 10.0
    assert policy.max_output_bytes == 1_000_000
    assert policy.max_error_bytes == 100_000
    assert policy.max_code_bytes == 100_000
    assert policy.max_memory_mb is None
    assert policy.allow_network is False
    assert "pandas" in policy.allowed_imports
    assert "os" in policy.blocked_imports


def test_invalid_timeout_rejected() -> None:
    """Verify invalid timeout values raise ValidationError."""
    with pytest.raises(ValidationError, match="timeout_seconds must be greater than 0"):
        PythonSandboxPolicy(timeout_seconds=0.0)

    with pytest.raises(ValidationError, match="timeout_seconds must be greater than 0"):
        PythonSandboxPolicy(timeout_seconds=-1.0)


def test_invalid_output_limit_rejected() -> None:
    """Verify invalid output/error byte limits raise ValidationError."""
    with pytest.raises(ValidationError, match="Byte limit values must be greater than 0"):
        PythonSandboxPolicy(max_output_bytes=0)

    with pytest.raises(ValidationError, match="Byte limit values must be greater than 0"):
        PythonSandboxPolicy(max_error_bytes=-100)


def test_invalid_code_limit_rejected() -> None:
    """Verify invalid max_code_bytes raises ValidationError."""
    with pytest.raises(ValidationError, match="Byte limit values must be greater than 0"):
        PythonSandboxPolicy(max_code_bytes=0)


def test_blocked_import_set_exists() -> None:
    """Verify DEFAULT_BLOCKED_IMPORTS contains standard high-risk modules."""
    for mod in ["os", "sys", "subprocess", "socket", "pathlib", "shutil", "ctypes"]:
        assert mod in DEFAULT_BLOCKED_IMPORTS


def test_configurable_allowed_imports() -> None:
    """Verify allowed_imports can be customized via constructor."""
    custom_policy = PythonSandboxPolicy(allowed_imports=frozenset({"math", "json"}))
    assert custom_policy.allowed_imports == frozenset({"math", "json"})
    assert "pandas" not in custom_policy.allowed_imports


def test_validate_python_code_success() -> None:
    """Verify valid code passes validate_python_code without errors."""
    policy = PythonSandboxPolicy()
    valid_code = "import math\nval = math.sqrt(16)\nresult = val + 1"
    validate_python_code(valid_code, policy)


def test_validate_python_code_syntax_error() -> None:
    """Verify invalid syntax raises PythonValidationError."""
    policy = PythonSandboxPolicy()
    with pytest.raises(PythonValidationError, match="Invalid Python syntax"):
        validate_python_code("def foo(:\n    pass", policy)
