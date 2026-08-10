"""Integration tests for DockerPythonExecutor requiring active Docker environment."""

import shutil
import subprocess

import pandas as pd
import pytest

from csv_analytics_agent.python_engine.models import PythonExecutionRequest
from csv_analytics_agent.python_engine.policy import PythonSandboxPolicy
from csv_analytics_agent.python_engine.sandbox import DockerPythonExecutor


def _is_docker_available() -> bool:
    """Check if docker executable is in PATH and daemon responds."""
    if not shutil.which("docker"):
        return False
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, timeout=3)
        return res.returncode == 0
    except Exception:
        return False


docker_required = pytest.mark.skipif(
    not _is_docker_available(),
    reason="Docker CLI / daemon is not available on test system",
)


@pytest.mark.docker
@docker_required
def test_docker_executor_scalar_analysis() -> None:
    """Verify scalar computation inside real Docker container."""
    policy = PythonSandboxPolicy(image_name="python:3.10-slim")
    executor = DockerPythonExecutor(policy=policy)
    df = pd.DataFrame({"sales": [10, 20, 30]})
    req = PythonExecutionRequest(code="total = df['sales'].sum()", question="Total sales?")

    res = executor.execute(req, df)
    assert res.success is True
    assert len(res.artifacts) == 1
    assert res.artifacts[0].data == 60


@pytest.mark.docker
@docker_required
def test_docker_executor_blocked_import() -> None:
    """Verify AST validation blocks forbidden import before container invocation."""
    executor = DockerPythonExecutor()
    df = pd.DataFrame({"a": [1]})
    req = PythonExecutionRequest(code="import os\nfiles = os.listdir('.')", question="Import test")

    res = executor.execute(req, df)
    assert res.success is False
    assert res.error_type == "PythonValidationError"
    assert "Import of blocked module 'os' is forbidden" in res.error_message
