"""Unit tests for Python engine domain exceptions."""

from csv_analytics_agent.exceptions.data_errors import CSVAnalyticsError
from csv_analytics_agent.python_engine.errors import (
    PythonArtifactError,
    PythonExecutionError,
    PythonOutputLimitError,
    PythonTimeoutError,
    PythonValidationError,
)


def test_exception_inheritance_hierarchy() -> None:
    """Verify python_engine domain exception inheritance tree."""
    assert issubclass(PythonExecutionError, CSVAnalyticsError)

    assert issubclass(PythonValidationError, PythonExecutionError)
    assert issubclass(PythonValidationError, ValueError)

    assert issubclass(PythonTimeoutError, PythonExecutionError)
    assert issubclass(PythonTimeoutError, TimeoutError)

    assert issubclass(PythonOutputLimitError, PythonExecutionError)
    assert issubclass(PythonOutputLimitError, ValueError)

    assert issubclass(PythonArtifactError, PythonExecutionError)
    assert issubclass(PythonArtifactError, ValueError)


def test_exception_instantiation() -> None:
    """Verify python_engine exceptions can be instantiated and raised."""
    err_val = PythonValidationError("Invalid Python code syntax.")
    assert str(err_val) == "Invalid Python code syntax."
    assert isinstance(err_val, CSVAnalyticsError)

    err_timeout = PythonTimeoutError("Execution exceeded 30s timeout.")
    assert isinstance(err_timeout, TimeoutError)
    assert isinstance(err_timeout, PythonExecutionError)

    err_limit = PythonOutputLimitError("Output size exceeds 10MB limit.")
    assert isinstance(err_limit, ValueError)

    err_artifact = PythonArtifactError("Artifact data payload is corrupt.")
    assert isinstance(err_artifact, PythonExecutionError)
