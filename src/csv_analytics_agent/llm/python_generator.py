"""LLM Python Code Generator for translating natural language queries into PythonExecutionRequest payloads.

CRITICAL ARCHITECTURAL BOUNDARY:
This module ONLY generates Python source code as a PythonExecutionRequest model.
It MUST NOT execute code, invoke subprocesses, call eval()/exec(), or interface with Docker.
Code execution is handled exclusively by BasePythonExecutor sandbox implementations.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage, SystemMessage

from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.llm.python_models import (
    GeneratedPythonProgram,
    PythonCodeGenerationError,
)

# Avoid importing execution backends or subprocess in generator
from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.python_engine.models import (
    PythonArtifactType,
    PythonExecutionRequest,
)

SYSTEM_PROMPT_TEMPLATE = """You are an expert Python data analysis code generator.
Your job is to generate Python code to answer analytical questions on a pandas DataFrame named `df`.

DATASET SCHEMA & PROFILES:
{schema_summary}

RETRIEVED COLUMNS:
{retrieved_columns_summary}

ADDITIONAL CONTEXT:
{additional_context}

CRITICAL RULES:
1. The DataFrame is pre-loaded as `df`. Do NOT read files from disk.
2. The code MUST assign its final answer to a variable named `result`.
3. Do NOT modify the original `df` inplace (avoid inplace=True).
4. Do NOT use filesystem access, network sockets, environment variables, credentials, or system calls.
5. Do NOT use dangerous functions (exec, eval, __import__, open, input, breakpoint).
6. Do NOT call external APIs, LLMs, or databases.
7. Do NOT attempt to run package management commands (pip, apt).
8. Use ONLY approved libraries: pandas, numpy, scipy, matplotlib, plotly.
9. Keep operations vectorized, efficient, and concise.
10. Ensure referenced column names match the dataset schema exactly.

Return your response matching the requested structured schema.
"""


class BasePythonCodeGenerator(ABC):
    """Abstract interface for LLM-powered Python code generation."""

    @abstractmethod
    def generate(
        self,
        question: str,
        schema: DatasetProfile | None = None,
        retrieved_columns: list[str] | None = None,
        context: str | None = None,
        dataset_hash: str | None = None,
    ) -> PythonExecutionRequest:
        """Generate a PythonExecutionRequest from user question and dataset schema.

        Args:
            question: Natural language user query.
            schema: Optional DatasetProfile containing dataset column metadata.
            retrieved_columns: Optional list of retrieved column name strings.
            context: Optional string containing relevant context.
            dataset_hash: Optional SHA-256 dataset hash.

        Returns:
            Validated PythonExecutionRequest instance.
        """
        ...


class GeminiPythonCodeGenerator(BasePythonCodeGenerator):
    """Gemini-powered Python code generator using BaseLLM abstraction."""

    def __init__(self, llm: BaseLLM | None = None) -> None:
        """Initialize GeminiPythonCodeGenerator with BaseLLM instance.

        Args:
            llm: Optional BaseLLM implementation (defaults to GeminiLLM()).
        """
        self._llm = llm or GeminiLLM()

    @property
    def llm(self) -> BaseLLM:
        """Return active BaseLLM instance."""
        return self._llm

    def _format_schema_summary(self, schema: DatasetProfile | None) -> str:
        if schema is None:
            return "No detailed schema profile provided."

        lines = [
            f"Dataset Summary: {schema.summary.row_count} rows, {schema.summary.column_count} columns",
            "Columns & Types:",
        ]
        for col_prof in schema.columns:
            lines.append(
                f" - `{col_prof.name}` ({col_prof.dtype}): {col_prof.missing_percentage:.1f}% missing"
            )
        return "\n".join(lines)

    def _validate_referenced_columns(
        self,
        program: GeneratedPythonProgram,
        schema: DatasetProfile | None,
    ) -> None:
        if schema is None or not schema.columns:
            return

        valid_cols = {col_prof.name for col_prof in schema.columns}
        for col in program.referenced_columns:
            if col and col not in valid_cols:
                raise PythonCodeGenerationError(
                    f"Generated code references unknown column '{col}' not present in dataset schema. "
                    f"Available columns: {sorted(list(valid_cols))}"
                )

    def generate(
        self,
        question: str,
        schema: DatasetProfile | None = None,
        retrieved_columns: list[str] | None = None,
        context: str | None = None,
        dataset_hash: str | None = None,
    ) -> PythonExecutionRequest:
        """Generate PythonExecutionRequest for target question using GeminiLLM.

        Args:
            question: User question string.
            schema: Optional DatasetProfile metadata.
            retrieved_columns: Optional list of retrieved column strings.
            context: Optional context string.
            dataset_hash: Optional dataset hash string.

        Returns:
            PythonExecutionRequest model.
        """
        if not question or not question.strip():
            raise PythonCodeGenerationError("User question must not be empty or whitespace-only.")

        retrieved = retrieved_columns or []
        schema_text = self._format_schema_summary(schema)
        retrieved_text = ", ".join(retrieved) if retrieved else "None"
        context_text = context or "None"

        system_msg = SystemMessage(
            content=SYSTEM_PROMPT_TEMPLATE.format(
                schema_summary=schema_text,
                retrieved_columns_summary=retrieved_text,
                additional_context=context_text,
            )
        )
        human_msg = HumanMessage(content=f"User Question: {question}")

        try:
            # Check if LLM supports structured output binding
            raw_llm = getattr(self._llm, "_llm", None)
            if raw_llm is not None and hasattr(raw_llm, "with_structured_output"):
                structured_llm = raw_llm.with_structured_output(GeneratedPythonProgram)
                res_obj = structured_llm.invoke([system_msg, human_msg])

                if isinstance(res_obj, GeneratedPythonProgram):
                    program = res_obj
                elif isinstance(res_obj, dict):
                    program = GeneratedPythonProgram(**res_obj)
                else:
                    raise PythonCodeGenerationError(
                        f"Structured output returned invalid payload type: {type(res_obj)}"
                    )
            else:
                # Fallback to invoking BaseLLM and parsing JSON payload
                json_prompt = (
                    f"{system_msg.content}\n\n"
                    "Respond ONLY with a valid JSON object matching this schema:\n"
                    '{\n  "code": "result = df[...]",\n  "explanation": "...",\n'
                    '  "expected_output_type": "table",\n  "dependencies": ["pandas"],\n'
                    '  "confidence": 1.0,\n  "referenced_columns": []\n}\n\n'
                    f"{human_msg.content}"
                )
                msg_res = self._llm.invoke(json_prompt)
                content_str = msg_res.content if hasattr(msg_res, "content") else str(msg_res)

                # Clean markdown blocks if present
                clean_json = str(content_str).strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.startswith("```"):
                    clean_json = clean_json[3:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]

                parsed_dict = json.loads(clean_json.strip())
                program = GeneratedPythonProgram(**parsed_dict)

        except PythonCodeGenerationError:
            raise
        except Exception as err:
            raise PythonCodeGenerationError(
                f"Failed to generate structured Python program from LLM: {err}"
            ) from err

        # Validate column names against schema if applicable
        self._validate_referenced_columns(program, schema)

        # Convert to PythonExecutionRequest
        metadata: dict[str, str | int | float | bool] = {
            "generator": "gemini",
            "model": self._llm.model_name,
            "expected_output_type": (
                program.expected_output_type.value
                if isinstance(program.expected_output_type, PythonArtifactType)
                else str(program.expected_output_type)
            ),
            "confidence": float(program.confidence),
            "explanation": str(program.explanation),
        }

        return PythonExecutionRequest(
            code=program.code,
            question=question,
            dataset_hash=dataset_hash,
            metadata=metadata,
        )


__all__ = [
    "BasePythonCodeGenerator",
    "GeminiPythonCodeGenerator",
]
