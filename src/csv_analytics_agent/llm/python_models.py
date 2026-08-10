"""Structured Pydantic domain models and exceptions for LLM Python code generation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from csv_analytics_agent.exceptions.data_errors import CSVAnalyticsError
from csv_analytics_agent.python_engine.models import PythonArtifactType


class PythonCodeGenerationError(CSVAnalyticsError):
    """Base exception for LLM Python code generation failures."""

    pass


class GeneratedPythonProgram(BaseModel):
    """Structured Pydantic output model requested from the LLM code generator.

    Attributes:
        code: Executable Python source code block.
        explanation: Natural language rationale explaining the code logic.
        expected_output_type: Primary expected PythonArtifactType classification.
        dependencies: List of imported Python package names.
        confidence: Generation confidence score (0.0 to 1.0).
        referenced_columns: List of dataset column names referenced in the code.
    """

    model_config = ConfigDict(frozen=True)

    code: str = Field(
        ..., description="Executable Python code block assigned to variable 'result'."
    )
    explanation: str = Field(
        ..., description="Brief explanation of analytical approach and code logic."
    )
    expected_output_type: PythonArtifactType = Field(
        default=PythonArtifactType.TABLE,
        description="Expected result artifact classification type.",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="List of Python library dependencies used in the generated code.",
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score float between 0.0 and 1.0.",
    )
    referenced_columns: list[str] = Field(
        default_factory=list,
        description="List of dataset column names explicitly referenced in the code.",
    )

    @field_validator("code", "explanation")
    @classmethod
    def _validate_non_empty_str(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field must not be empty or whitespace-only.")
        return value

    @field_validator("confidence")
    @classmethod
    def _validate_confidence_range(cls, value: float) -> float:
        if not (0.0 <= value <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0.")
        return value


__all__ = [
    "GeneratedPythonProgram",
    "PythonCodeGenerationError",
]
