"""Subprocess and Container Python Sandbox Executors.

Security Limitation Note: Python execution is isolated using a restricted subprocess
for local development and an optional container backend for stronger isolation.
Container isolation is not equivalent to a formally verified sandbox or microVM.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from csv_analytics_agent.python_engine.backends import (
    BaseSandboxBackend,
    DockerBackend,
    SubprocessBackend,
)
from csv_analytics_agent.python_engine.base import BasePythonExecutor
from csv_analytics_agent.python_engine.models import (
    PythonExecutionRequest,
    PythonExecutionResult,
)
from csv_analytics_agent.python_engine.policy import PythonSandboxPolicy


class PythonSandboxExecutor(BasePythonExecutor):
    """Subprocess-based executor running validated Python code in an isolated local directory."""

    def __init__(
        self,
        policy: PythonSandboxPolicy | None = None,
        backend: BaseSandboxBackend | None = None,
    ) -> None:
        """Initialize PythonSandboxExecutor with an optional policy and backend.

        Args:
            policy: Optional PythonSandboxPolicy instance.
            backend: Optional BaseSandboxBackend instance (defaults to SubprocessBackend).
        """
        self._policy = policy or PythonSandboxPolicy()
        self._backend = backend or SubprocessBackend()

    @property
    def executor_name(self) -> str:
        """Return the programmatic identifier name of the sandbox executor."""
        return f"python-sandbox-{self._backend.backend_name}"

    @property
    def policy(self) -> PythonSandboxPolicy:
        """Return active sandbox policy."""
        return self._policy

    @property
    def backend(self) -> BaseSandboxBackend:
        """Return active sandbox backend."""
        return self._backend

    def execute(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
    ) -> PythonExecutionResult:
        """Execute Python code against target DataFrame within backend boundary.

        Args:
            request: PythonExecutionRequest containing code and execution options.
            dataframe: Target pandas DataFrame context.

        Returns:
            PythonExecutionResult containing success status, outputs, and artifacts.
        """
        return self._backend.run_code(request, dataframe, self._policy)


class DockerPythonExecutor(BasePythonExecutor):
    """Docker container-based executor running validated Python code in an isolated container."""

    def __init__(
        self,
        policy: PythonSandboxPolicy | None = None,
        backend: DockerBackend | None = None,
    ) -> None:
        """Initialize DockerPythonExecutor with an optional policy and DockerBackend.

        Args:
            policy: Optional PythonSandboxPolicy instance.
            backend: Optional DockerBackend instance.
        """
        self._policy = policy or PythonSandboxPolicy()
        self._backend = backend or DockerBackend()

    @property
    def executor_name(self) -> str:
        """Return programmatic identifier name of Docker executor."""
        return "python-sandbox-docker"

    @property
    def policy(self) -> PythonSandboxPolicy:
        """Return active sandbox policy."""
        return self._policy

    @property
    def backend(self) -> DockerBackend:
        """Return active Docker backend."""
        return self._backend

    def execute(
        self,
        request: PythonExecutionRequest,
        dataframe: pd.DataFrame,
    ) -> PythonExecutionResult:
        """Execute Python code against target DataFrame inside an isolated Docker container.

        Args:
            request: PythonExecutionRequest containing code and execution options.
            dataframe: Target pandas DataFrame context.

        Returns:
            PythonExecutionResult containing success status, outputs, and artifacts.
        """
        return self._backend.run_code(request, dataframe, self._policy)


# Alias for ContainerPythonExecutor
ContainerPythonExecutor = DockerPythonExecutor


def create_python_executor(
    settings: Any | None = None,
    mode: str | None = None,
    policy: PythonSandboxPolicy | None = None,
) -> BasePythonExecutor:
    """Factory function constructing BasePythonExecutor based on settings or mode.

    Args:
        settings: Optional Settings object or dictionary containing configuration.
        mode: Optional explicit execution mode string ('subprocess' or 'container' / 'docker').
        policy: Optional PythonSandboxPolicy override.

    Returns:
        Configured BasePythonExecutor instance (PythonSandboxExecutor or DockerPythonExecutor).
    """
    effective_mode = mode

    if effective_mode is None and settings is not None:
        if hasattr(settings, "python_execution_backend"):
            effective_mode = str(settings.python_execution_backend)
        elif isinstance(settings, dict):
            effective_mode = str(settings.get("python_execution_backend", "subprocess"))

    if effective_mode is None:
        effective_mode = "subprocess"

    effective_policy = policy
    if effective_policy is None and settings is not None:
        kwargs: dict[str, Any] = {}
        if hasattr(settings, "python_sandbox_image"):
            kwargs["image_name"] = str(settings.python_sandbox_image)
        if hasattr(settings, "python_sandbox_memory_mb"):
            kwargs["memory_mb"] = int(settings.python_sandbox_memory_mb)
        if hasattr(settings, "python_sandbox_cpu_limit"):
            kwargs["cpu_limit"] = float(settings.python_sandbox_cpu_limit)
        if hasattr(settings, "python_sandbox_pids_limit"):
            kwargs["pids_limit"] = int(settings.python_sandbox_pids_limit)
        if hasattr(settings, "python_sandbox_timeout_seconds"):
            kwargs["timeout_seconds"] = float(settings.python_sandbox_timeout_seconds)
        if hasattr(settings, "python_sandbox_network"):
            kwargs["allow_network"] = bool(settings.python_sandbox_network)

        if kwargs:
            effective_policy = PythonSandboxPolicy(**kwargs)

    effective_policy = effective_policy or PythonSandboxPolicy()

    if str(effective_mode).lower() in ("container", "docker"):
        return DockerPythonExecutor(policy=effective_policy)

    return PythonSandboxExecutor(policy=effective_policy)


__all__ = [
    "ContainerPythonExecutor",
    "DockerPythonExecutor",
    "PythonSandboxExecutor",
    "create_python_executor",
]
