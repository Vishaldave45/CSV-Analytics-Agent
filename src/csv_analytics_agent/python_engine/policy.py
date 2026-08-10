"""Security policy definitions and AST code validation for Python Execution Engine."""

from __future__ import annotations

import ast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from csv_analytics_agent.python_engine.errors import PythonValidationError

DEFAULT_ALLOWED_IMPORTS: frozenset[str] = frozenset(
    {
        "math",
        "statistics",
        "json",
        "datetime",
        "collections",
        "itertools",
        "functools",
        "pandas",
        "numpy",
        "scipy",
        "matplotlib",
        "plotly",
    }
)

DEFAULT_BLOCKED_IMPORTS: frozenset[str] = frozenset(
    {
        "os",
        "sys",
        "subprocess",
        "socket",
        "pathlib",
        "shutil",
        "ctypes",
        "multiprocessing",
        "signal",
        "importlib",
    }
)


class PythonSandboxPolicy(BaseModel):
    """Configuration policy defining execution limits and security restrictions.

    Attributes:
        timeout_seconds: Maximum allowed subprocess execution time in seconds.
        max_output_bytes: Maximum allowed standard output byte size.
        max_error_bytes: Maximum allowed standard error byte size.
        max_code_bytes: Maximum allowed input Python code size in bytes.
        max_memory_mb: Optional maximum process memory limit in megabytes.
        allowed_imports: Frozenset of permitted top-level Python module names.
        blocked_imports: Frozenset of explicitly forbidden Python module names.
        allow_network: Flag indicating whether network connections are permitted.
    """

    model_config = ConfigDict(frozen=True)

    timeout_seconds: float = Field(
        default=10.0,
        description="Maximum execution timeout in seconds.",
    )
    max_output_bytes: int = Field(
        default=1_000_000,
        description="Maximum allowed stdout size in bytes.",
    )
    max_error_bytes: int = Field(
        default=100_000,
        description="Maximum allowed stderr size in bytes.",
    )
    max_code_bytes: int = Field(
        default=100_000,
        description="Maximum allowed Python code size in bytes.",
    )
    max_memory_mb: int | None = Field(
        default=None,
        description="Optional maximum memory limit in megabytes.",
    )
    memory_mb: int = Field(
        default=512,
        description="Memory limit in megabytes for sandbox process/container.",
    )
    cpu_limit: float = Field(
        default=1.0,
        description="CPU limit core count for sandbox execution.",
    )
    pids_limit: int = Field(
        default=64,
        description="Maximum process PID count limit for sandbox execution.",
    )
    image_name: str = Field(
        default="csv-analytics-python:latest",
        description="Docker image name for containerized execution.",
    )
    allowed_imports: frozenset[str] = Field(
        default=DEFAULT_ALLOWED_IMPORTS,
        description="Frozenset of allowed top-level module names.",
    )
    blocked_imports: frozenset[str] = Field(
        default=DEFAULT_BLOCKED_IMPORTS,
        description="Frozenset of forbidden module names.",
    )
    allow_network: bool = Field(
        default=False,
        description="Whether network access is permitted (default False).",
    )

    @field_validator("timeout_seconds")
    @classmethod
    def _validate_timeout(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")
        return value

    @field_validator("max_output_bytes", "max_error_bytes", "max_code_bytes")
    @classmethod
    def _validate_positive_bytes(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Byte limit values must be greater than 0.")
        return value

    @field_validator("memory_mb", "pids_limit")
    @classmethod
    def _validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Value must be greater than 0.")
        return value

    @field_validator("cpu_limit")
    @classmethod
    def _validate_positive_float(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("cpu_limit must be greater than 0.")
        return value

    @field_validator("image_name")
    @classmethod
    def _validate_image_name(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("image_name must not be empty or whitespace-only.")
        return value


class _SecurityASTVisitor(ast.NodeVisitor):
    """AST Visitor enforcing PythonSandboxPolicy import and builtin restrictions."""

    FORBIDDEN_IDENTIFIERS: frozenset[str] = frozenset(
        {
            "exec",
            "eval",
            "compile",
            "__import__",
            "breakpoint",
            "open",
            "input",
        }
    )

    FORBIDDEN_ATTRIBUTES: frozenset[str] = frozenset(
        {
            "__subclasses__",
            "__globals__",
            "__code__",
            "__closure__",
            "__builtins__",
            "__import__",
            "__bases__",
            "__mro__",
            "__class__",
        }
    )

    def __init__(self, policy: PythonSandboxPolicy) -> None:
        self.policy = policy

    def _check_module(self, module_name: str) -> None:
        top_level = module_name.split(".")[0]
        if top_level in self.policy.blocked_imports:
            raise PythonValidationError(f"Import of blocked module '{top_level}' is forbidden.")
        if top_level not in self.policy.allowed_imports:
            raise PythonValidationError(f"Import of unapproved module '{top_level}' is forbidden.")

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_module(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self._check_module(node.module)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in self.FORBIDDEN_IDENTIFIERS:
            raise PythonValidationError(
                f"Use of forbidden function or identifier '{node.id}' is forbidden."
            )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in self.FORBIDDEN_ATTRIBUTES:
            raise PythonValidationError(
                f"Access to dangerous attribute '{node.attr}' is forbidden."
            )
        self.generic_visit(node)


def validate_python_code(
    code: str,
    policy: PythonSandboxPolicy,
) -> None:
    """Validate code size, syntax, and security rules against PythonSandboxPolicy.

    Args:
        code: Python source code string to validate.
        policy: PythonSandboxPolicy instance containing security rules.

    Raises:
        PythonValidationError: If code size, syntax, imports, or AST nodes violate policy.
    """
    code_bytes = len(code.encode("utf-8"))
    if code_bytes > policy.max_code_bytes:
        raise PythonValidationError(
            f"Code size ({code_bytes} bytes) exceeds maximum limit of {policy.max_code_bytes} bytes."
        )

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise PythonValidationError(f"Invalid Python syntax: {exc}") from exc

    visitor = _SecurityASTVisitor(policy)
    visitor.visit(tree)


__all__ = [
    "DEFAULT_ALLOWED_IMPORTS",
    "DEFAULT_BLOCKED_IMPORTS",
    "PythonSandboxPolicy",
    "validate_python_code",
]
