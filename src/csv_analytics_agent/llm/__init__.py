"""LLM abstraction, provider, and Python code generation package."""

from typing import Any

from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.llm.python_generator import (
    BasePythonCodeGenerator,
    GeminiPythonCodeGenerator,
)
from csv_analytics_agent.llm.python_models import (
    GeneratedPythonProgram,
    PythonCodeGenerationError,
)
from csv_analytics_agent.llm.rate_limiter import build_gemini_limiter

GeminiLLM: type[Any] | None = None

try:
    from csv_analytics_agent.llm.gemini import GeminiLLM as _GeminiLLM

    GeminiLLM = _GeminiLLM
except ImportError:  # pragma: no cover
    pass

__all__ = [
    "BaseLLM",
    "BasePythonCodeGenerator",
    "GeminiLLM",
    "GeminiPythonCodeGenerator",
    "GeneratedPythonProgram",
    "PythonCodeGenerationError",
    "build_gemini_limiter",
]
