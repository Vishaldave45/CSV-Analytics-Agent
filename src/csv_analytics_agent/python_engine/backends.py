"""Sandbox execution backends for Python Execution Engine."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd

from csv_analytics_agent.python_engine.errors import (
    PythonValidationError,
)
from csv_analytics_agent.python_engine.models import (
    PythonArtifact,
    PythonArtifactType,
    PythonExecutionRequest,
    PythonExecutionResult,
)
from csv_analytics_agent.python_engine.policy import (
    PythonSandboxPolicy,
    validate_python_code,
)

RUNNER_SCRIPT_CONTENT = """
import sys
import io
import json
import base64
import traceback
import pandas as pd
import numpy as np

def run_script():
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    orig_stdout, orig_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = stdout_buf, stderr_buf

    user_globals = {
        "df": pd.read_csv("dataset.csv"),
        "pd": pd,
        "np": np,
        "__name__": "__main__",
        "__doc__": None,
    }

    error_type = None
    error_message = None
    success = True
    artifacts = []

    try:
        with open("user_code.py", "r", encoding="utf-8") as f:
            code_text = f.read()
        compiled_code = compile(code_text, "user_code.py", "exec")
        exec(compiled_code, user_globals)
    except Exception as exc:
        success = False
        error_type = type(exc).__name__
        error_message = str(exc)
        traceback.print_exc(file=sys.stderr)
    finally:
        sys.stdout, sys.stderr = orig_stdout, orig_stderr

    captured_stdout = stdout_buf.getvalue()
    captured_stderr = stderr_buf.getvalue()

    if success:
        try:
            import matplotlib.pyplot as plt
            if plt.get_fignums():
                img_buf = io.BytesIO()
                plt.savefig(img_buf, format="png", bbox_inches="tight")
                plt.close("all")
                artifacts.append({
                    "artifact_type": "image",
                    "name": "matplotlib_chart",
                    "mime_type": "image/png",
                    "data_b64": base64.b64encode(img_buf.getvalue()).decode("utf-8"),
                    "metadata": {},
                })
        except Exception:
            pass

        ignored = {"df", "pd", "np", "__name__", "__doc__", "__package__", "__builtins__"}
        user_vars = [k for k in user_globals.keys() if k not in ignored and not k.startswith("_")]

        for name in user_vars:
            val = user_globals[name]

            # Matplotlib figure object
            try:
                import matplotlib.figure
                if isinstance(val, matplotlib.figure.Figure):
                    img_buf = io.BytesIO()
                    val.savefig(img_buf, format="png", bbox_inches="tight")
                    artifacts.append({
                        "artifact_type": "image",
                        "name": name,
                        "mime_type": "image/png",
                        "data_b64": base64.b64encode(img_buf.getvalue()).decode("utf-8"),
                        "metadata": {},
                    })
                    continue
            except Exception:
                pass

            # Plotly figure object
            try:
                if hasattr(val, "to_dict") and callable(getattr(val, "to_dict")):
                    val_module = type(val).__module__
                    if "plotly" in val_module:
                        artifacts.append({
                            "artifact_type": "interactive",
                            "name": name,
                            "mime_type": "application/json",
                            "data_json": val.to_dict(),
                            "metadata": {},
                        })
                        continue
            except Exception:
                pass

            # Pandas DataFrame
            if isinstance(val, pd.DataFrame):
                artifacts.append({
                    "artifact_type": "dataframe",
                    "name": name,
                    "mime_type": "application/json",
                    "data_json": json.loads(val.to_json(orient="split")),
                    "metadata": {},
                })
            # Pandas Series
            elif isinstance(val, pd.Series):
                artifacts.append({
                    "artifact_type": "table",
                    "name": name,
                    "mime_type": "application/json",
                    "data_json": {"index": list(val.index), "name": str(val.name or name), "data": list(val.values)},
                    "metadata": {},
                })
            # Scalar
            elif isinstance(val, (int, float, bool)):
                artifacts.append({
                    "artifact_type": "scalar",
                    "name": name,
                    "mime_type": None,
                    "data_json": val,
                    "metadata": {},
                })
            # String
            elif isinstance(val, str):
                artifacts.append({
                    "artifact_type": "text",
                    "name": name,
                    "mime_type": "text/plain",
                    "data_json": val,
                    "metadata": {},
                })

    res_payload = {
        "success": success,
        "stdout": captured_stdout,
        "stderr": captured_stderr,
        "error_type": error_type,
        "error_message": error_message,
        "artifacts": artifacts,
    }

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(res_payload, f)

if __name__ == "__main__":
    run_script()
"""


class BaseSandboxBackend(ABC):
    """Abstract interface defining execution operations for sandbox isolation backends."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return the programmatic name identifier of the backend implementation."""
        ...

    @abstractmethod
    def run_code(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
        policy: PythonSandboxPolicy,
    ) -> PythonExecutionResult:
        """Execute validated Python code within the backend's isolation boundary."""
        ...


class SubprocessBackend(BaseSandboxBackend):
    """Subprocess-based sandbox execution backend."""

    @property
    def backend_name(self) -> str:
        return "subprocess"

    def run_code(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
        policy: PythonSandboxPolicy,
    ) -> PythonExecutionResult:
        start_time = time.perf_counter()

        try:
            validate_python_code(request.code, policy)
        except PythonValidationError as err:
            execution_time_ms = (time.perf_counter() - start_time) * 1000.0
            return PythonExecutionResult(
                success=False,
                stdout="",
                stderr="",
                execution_time_ms=execution_time_ms,
                error_type="PythonValidationError",
                error_message=str(err),
            )

        effective_timeout = min(request.timeout_seconds, policy.timeout_seconds)
        effective_max_out = min(request.max_output_bytes, policy.max_output_bytes)
        effective_max_err = policy.max_error_bytes

        with tempfile.TemporaryDirectory(prefix="py_sandbox_") as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            dataframe.to_csv(temp_dir / "dataset.csv", index=False)
            (temp_dir / "user_code.py").write_text(request.code, encoding="utf-8")
            (temp_dir / "runner.py").write_text(RUNNER_SCRIPT_CONTENT, encoding="utf-8")

            clean_env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "PYTHONUNBUFFERED": "1",
                "LC_ALL": "C.UTF-8",
                "LANG": "C.UTF-8",
            }

            cmd = [sys.executable, "-I", "-B", str(temp_dir / "runner.py")]

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(temp_dir),
                    env=clean_env,
                    capture_output=True,
                    text=True,
                    timeout=effective_timeout,
                )
                execution_time_ms = (time.perf_counter() - start_time) * 1000.0
            except subprocess.TimeoutExpired:
                execution_time_ms = (time.perf_counter() - start_time) * 1000.0
                return PythonExecutionResult(
                    success=False,
                    stdout="",
                    stderr="Execution timed out.",
                    execution_time_ms=execution_time_ms,
                    error_type="PythonTimeoutError",
                    error_message=f"Execution exceeded timeout limit of {effective_timeout}s.",
                )

            result_json_path = temp_dir / "result.json"
            if not result_json_path.exists():
                return PythonExecutionResult(
                    success=False,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    execution_time_ms=execution_time_ms,
                    error_type="PythonExecutionError",
                    error_message=proc.stderr.strip()
                    or f"Process exited with code {proc.returncode}.",
                )

            try:
                raw_result = json.loads(result_json_path.read_text(encoding="utf-8"))
            except Exception as err:
                return PythonExecutionResult(
                    success=False,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    execution_time_ms=execution_time_ms,
                    error_type="PythonExecutionError",
                    error_message=f"Failed to parse result payload: {err}",
                )

            captured_stdout = raw_result.get("stdout") or proc.stdout
            captured_stderr = raw_result.get("stderr") or proc.stderr

            stdout_bytes = len(captured_stdout.encode("utf-8"))
            stderr_bytes = len(captured_stderr.encode("utf-8"))
            if stdout_bytes > effective_max_out or stderr_bytes > effective_max_err:
                return PythonExecutionResult(
                    success=False,
                    stdout=captured_stdout[:1000] + "\n... [TRUNCATED]",
                    stderr=captured_stderr[:1000] + "\n... [TRUNCATED]",
                    execution_time_ms=execution_time_ms,
                    error_type="PythonOutputLimitError",
                    error_message=(
                        f"Output size ({stdout_bytes} stdout, {stderr_bytes} stderr bytes) "
                        f"exceeded maximum allowed limit."
                    ),
                )

            artifacts: list[PythonArtifact] = []
            for art_data in raw_result.get("artifacts", []):
                art_type = PythonArtifactType(art_data["artifact_type"])
                name = art_data["name"]
                mime_type = art_data.get("mime_type")
                meta = art_data.get("metadata", {})

                payload: Any = None
                if "data_b64" in art_data:
                    payload = base64.b64decode(art_data["data_b64"])
                elif "data_json" in art_data:
                    json_val = art_data["data_json"]
                    if art_type == PythonArtifactType.DATAFRAME and isinstance(json_val, dict):
                        payload = pd.DataFrame(
                            json_val.get("data"),
                            columns=json_val.get("columns"),
                            index=json_val.get("index"),
                        )
                    else:
                        payload = json_val

                artifacts.append(
                    PythonArtifact(
                        artifact_type=art_type,
                        name=name,
                        mime_type=mime_type,
                        data=payload,
                        metadata=meta,
                    )
                )

            return PythonExecutionResult(
                success=raw_result.get("success", False),
                stdout=raw_result.get("stdout", proc.stdout),
                stderr=raw_result.get("stderr", proc.stderr),
                artifacts=artifacts,
                execution_time_ms=execution_time_ms,
                error_type=raw_result.get("error_type"),
                error_message=raw_result.get("error_message"),
                metadata={"backend": self.backend_name},
            )


class DockerBackend(BaseSandboxBackend):
    """Docker container-based sandbox execution backend."""

    @property
    def backend_name(self) -> str:
        return "container"

    def build_docker_command(
        self,
        temp_dir: Path,
        container_name: str,
        policy: PythonSandboxPolicy,
    ) -> list[str]:
        """Construct Docker run command with strict security flags."""
        network_flag = "none" if not policy.allow_network else "bridge"
        return [
            "docker",
            "run",
            "--name",
            container_name,
            "--rm",
            "--network",
            network_flag,
            "--user",
            "1000:1000",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--memory",
            f"{policy.memory_mb}m",
            "--cpus",
            str(policy.cpu_limit),
            "--pids-limit",
            str(policy.pids_limit),
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "-v",
            f"{temp_dir.resolve()}:/workspace:rw",
            "-w",
            "/workspace",
            "-e",
            "PYTHONUNBUFFERED=1",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            policy.image_name,
            "python3",
            "-I",
            "-B",
            "runner.py",
        ]

    def run_code(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
        policy: PythonSandboxPolicy,
    ) -> PythonExecutionResult:
        start_time = time.perf_counter()

        # Step 1: Layered AST Validation
        try:
            validate_python_code(request.code, policy)
        except PythonValidationError as err:
            execution_time_ms = (time.perf_counter() - start_time) * 1000.0
            return PythonExecutionResult(
                success=False,
                stdout="",
                stderr="",
                execution_time_ms=execution_time_ms,
                error_type="PythonValidationError",
                error_message=str(err),
            )

        effective_timeout = min(request.timeout_seconds, policy.timeout_seconds)
        effective_max_out = min(request.max_output_bytes, policy.max_output_bytes)
        effective_max_err = policy.max_error_bytes

        with tempfile.TemporaryDirectory(prefix="docker_sandbox_") as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            dataframe.to_csv(temp_dir / "dataset.csv", index=False)
            (temp_dir / "user_code.py").write_text(request.code, encoding="utf-8")
            (temp_dir / "runner.py").write_text(RUNNER_SCRIPT_CONTENT, encoding="utf-8")

            container_name = f"csv_agent_sbx_{uuid.uuid4().hex[:8]}"
            cmd = self.build_docker_command(temp_dir, container_name, policy)

            clean_env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}

            try:
                proc = subprocess.run(
                    cmd,
                    env=clean_env,
                    capture_output=True,
                    text=True,
                    timeout=effective_timeout,
                )
                execution_time_ms = (time.perf_counter() - start_time) * 1000.0

            except subprocess.TimeoutExpired:
                execution_time_ms = (time.perf_counter() - start_time) * 1000.0
                # Force cleanup container if still running
                subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True,
                    text=True,
                )
                return PythonExecutionResult(
                    success=False,
                    stdout="",
                    stderr="Execution timed out inside container.",
                    execution_time_ms=execution_time_ms,
                    error_type="PythonTimeoutError",
                    error_message=f"Execution exceeded timeout limit of {effective_timeout}s.",
                )
            except Exception as exc:
                execution_time_ms = (time.perf_counter() - start_time) * 1000.0
                return PythonExecutionResult(
                    success=False,
                    stdout="",
                    stderr=str(exc),
                    execution_time_ms=execution_time_ms,
                    error_type="PythonExecutionError",
                    error_message=f"Docker backend failed: {exc}",
                )

            result_json_path = temp_dir / "result.json"
            if not result_json_path.exists():
                return PythonExecutionResult(
                    success=False,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    execution_time_ms=execution_time_ms,
                    error_type="PythonExecutionError",
                    error_message=proc.stderr.strip()
                    or f"Container process exited with code {proc.returncode}.",
                )

            try:
                raw_result = json.loads(result_json_path.read_text(encoding="utf-8"))
            except Exception as err:
                return PythonExecutionResult(
                    success=False,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    execution_time_ms=execution_time_ms,
                    error_type="PythonExecutionError",
                    error_message=f"Failed to parse container result payload: {err}",
                )

            captured_stdout = raw_result.get("stdout") or proc.stdout
            captured_stderr = raw_result.get("stderr") or proc.stderr

            stdout_bytes = len(captured_stdout.encode("utf-8"))
            stderr_bytes = len(captured_stderr.encode("utf-8"))
            if stdout_bytes > effective_max_out or stderr_bytes > effective_max_err:
                return PythonExecutionResult(
                    success=False,
                    stdout=captured_stdout[:1000] + "\n... [TRUNCATED]",
                    stderr=captured_stderr[:1000] + "\n... [TRUNCATED]",
                    execution_time_ms=execution_time_ms,
                    error_type="PythonOutputLimitError",
                    error_message=(
                        f"Output size ({stdout_bytes} stdout, {stderr_bytes} stderr bytes) "
                        f"exceeded maximum allowed limit."
                    ),
                )

            artifacts: list[PythonArtifact] = []
            for art_data in raw_result.get("artifacts", []):
                art_type = PythonArtifactType(art_data["artifact_type"])
                name = art_data["name"]
                mime_type = art_data.get("mime_type")
                meta = art_data.get("metadata", {})

                payload: Any = None
                if "data_b64" in art_data:
                    payload = base64.b64decode(art_data["data_b64"])
                elif "data_json" in art_data:
                    json_val = art_data["data_json"]
                    if art_type == PythonArtifactType.DATAFRAME and isinstance(json_val, dict):
                        payload = pd.DataFrame(
                            json_val.get("data"),
                            columns=json_val.get("columns"),
                            index=json_val.get("index"),
                        )
                    else:
                        payload = json_val

                artifacts.append(
                    PythonArtifact(
                        artifact_type=art_type,
                        name=name,
                        mime_type=mime_type,
                        data=payload,
                        metadata=meta,
                    )
                )

            return PythonExecutionResult(
                success=raw_result.get("success", False),
                stdout=raw_result.get("stdout", proc.stdout),
                stderr=raw_result.get("stderr", proc.stderr),
                artifacts=artifacts,
                execution_time_ms=execution_time_ms,
                error_type=raw_result.get("error_type"),
                error_message=raw_result.get("error_message"),
                metadata={"backend": self.backend_name},
            )


__all__ = [
    "BaseSandboxBackend",
    "DockerBackend",
    "SubprocessBackend",
]
