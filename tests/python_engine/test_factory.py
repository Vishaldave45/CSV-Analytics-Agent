"""Unit tests for create_python_executor factory function."""

from csv_analytics_agent.config.setting import Settings
from csv_analytics_agent.python_engine.policy import PythonSandboxPolicy
from csv_analytics_agent.python_engine.sandbox import (
    DockerPythonExecutor,
    PythonSandboxExecutor,
    create_python_executor,
)


def test_factory_default_mode() -> None:
    """Verify default mode creates PythonSandboxExecutor (subprocess)."""
    executor = create_python_executor()
    assert isinstance(executor, PythonSandboxExecutor)
    assert "subprocess" in executor.executor_name


def test_factory_explicit_container_mode() -> None:
    """Verify mode='container' or mode='docker' creates DockerPythonExecutor."""
    exec_container = create_python_executor(mode="container")
    assert isinstance(exec_container, DockerPythonExecutor)

    exec_docker = create_python_executor(mode="docker")
    assert isinstance(exec_docker, DockerPythonExecutor)


def test_factory_settings_driven_creation() -> None:
    """Verify Settings object drives backend selection and policy options."""
    settings = Settings(
        python_execution_backend="container",
        python_sandbox_memory_mb=256,
        python_sandbox_cpu_limit=0.5,
    )
    executor = create_python_executor(settings=settings)
    assert isinstance(executor, DockerPythonExecutor)
    assert executor.policy.memory_mb == 256
    assert executor.policy.cpu_limit == 0.5


def test_factory_custom_policy_override() -> None:
    """Verify custom policy parameter overrides settings."""
    custom_policy = PythonSandboxPolicy(memory_mb=1024, cpu_limit=2.0)
    executor = create_python_executor(mode="subprocess", policy=custom_policy)
    assert isinstance(executor, PythonSandboxExecutor)
    assert executor.policy.memory_mb == 1024
    assert executor.policy.cpu_limit == 2.0
