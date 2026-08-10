"""Unit tests for Python engine sandbox backends (SubprocessBackend and DockerBackend)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from csv_analytics_agent.python_engine.backends import DockerBackend, SubprocessBackend
from csv_analytics_agent.python_engine.models import PythonExecutionRequest
from csv_analytics_agent.python_engine.policy import PythonSandboxPolicy


def test_subprocess_backend_name() -> None:
    """Verify SubprocessBackend backend_name identifier."""
    backend = SubprocessBackend()
    assert backend.backend_name == "subprocess"


def test_docker_backend_name() -> None:
    """Verify DockerBackend backend_name identifier."""
    backend = DockerBackend()
    assert backend.backend_name == "container"


def test_docker_backend_build_command() -> None:
    """Verify DockerBackend.build_docker_command constructs correct security flags."""
    backend = DockerBackend()
    policy = PythonSandboxPolicy(
        memory_mb=256,
        cpu_limit=0.5,
        pids_limit=32,
        allow_network=False,
        image_name="test-sandbox:v1",
    )
    temp_dir = Path("/tmp/mock_sandbox")

    cmd = backend.build_docker_command(temp_dir, "test_container_123", policy)

    assert "docker" in cmd
    assert "run" in cmd
    assert "--name" in cmd
    assert "test_container_123" in cmd
    assert "--rm" in cmd
    assert "--network" in cmd
    assert "none" in cmd
    assert "--user" in cmd
    assert "1000:1000" in cmd
    assert "--read-only" in cmd
    assert "--cap-drop=ALL" in cmd
    assert "--security-opt" in cmd
    assert "no-new-privileges:true" in cmd
    assert "--memory" in cmd
    assert "256m" in cmd
    assert "--cpus" in cmd
    assert "0.5" in cmd
    assert "--pids-limit" in cmd
    assert "32" in cmd
    assert "test-sandbox:v1" in cmd


@patch("csv_analytics_agent.python_engine.backends.subprocess.run")
def test_docker_backend_run_code_mocked(mock_subproc_run: MagicMock) -> None:
    """Verify DockerBackend.run_code invokes subprocess with clean env and docker flags."""
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "Container stdout"
    mock_proc.stderr = ""
    mock_subproc_run.return_value = mock_proc

    backend = DockerBackend()
    policy = PythonSandboxPolicy()
    req = PythonExecutionRequest(code="x = 10", question="test question")
    df = pd.DataFrame({"col": [1, 2]})

    # Mock file existence for result.json
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "pathlib.Path.read_text",
            return_value='{"success": true, "stdout": "ok", "stderr": "", "artifacts": []}',
        ),
    ):
        result = backend.run_code(req, df, policy)

    assert result.success is True
    assert result.metadata["backend"] == "container"
    assert mock_subproc_run.called
