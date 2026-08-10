"""Deterministic unit tests and golden regression tests for LLM Python code generator."""

import ast
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from langchain_core.messages import AIMessage, BaseMessage

from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.llm.gemini import GeminiLLM
from csv_analytics_agent.llm.python_generator import GeminiPythonCodeGenerator
from csv_analytics_agent.llm.python_models import (
    GeneratedPythonProgram,
    PythonCodeGenerationError,
)
from csv_analytics_agent.profiler import DatasetProfiler
from csv_analytics_agent.python_engine.models import (
    PythonArtifactType,
    PythonExecutionRequest,
)


class FakeBaseLLM(BaseLLM):
    """Deterministic Fake BaseLLM implementation returning controlled responses."""

    def __init__(self, response_program: GeneratedPythonProgram | None = None) -> None:
        self._response_program = response_program or GeneratedPythonProgram(
            code="result = df['revenue'].mean()",
            explanation="Calculated mean revenue.",
            expected_output_type=PythonArtifactType.SCALAR,
            dependencies=["pandas"],
            confidence=0.95,
            referenced_columns=["revenue"],
        )
        self.last_input: Any = None

    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        return self

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        self.last_input = input_data
        json_payload = self._response_program.model_dump_json()
        return AIMessage(content=json_payload)

    def stream(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> Any:
        yield self.invoke(input_data)

    @property
    def model_name(self) -> str:
        return "fake-gemini-model"


@pytest.fixture
def sample_profile() -> Any:
    """Fixture providing a sample DatasetProfile."""
    df = pd.DataFrame(
        {
            "category": ["A", "B", "A", "C"],
            "unit_price": [10.0, 20.0, 15.0, 30.0],
            "quantity": [2, 1, 4, 3],
            "revenue": [20.0, 20.0, 60.0, 90.0],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        }
    )
    return DatasetProfiler().profile(df)


# 1. Valid structured response produces PythonExecutionRequest
def test_valid_structured_response_produces_request(sample_profile: Any) -> None:
    fake_llm = FakeBaseLLM()
    generator = GeminiPythonCodeGenerator(llm=fake_llm)
    req = generator.generate("What is average revenue?", schema=sample_profile)

    assert isinstance(req, PythonExecutionRequest)


# 2. Code is preserved
def test_code_is_preserved(sample_profile: Any) -> None:
    program = GeneratedPythonProgram(
        code="result = df.groupby('category')['revenue'].sum().reset_index()",
        explanation="Sum revenue by category",
        expected_output_type=PythonArtifactType.TABLE,
        referenced_columns=["category", "revenue"],
    )
    generator = GeminiPythonCodeGenerator(llm=FakeBaseLLM(program))
    req = generator.generate("Revenue by category?", schema=sample_profile)

    assert req.code == program.code


# 3. Question is preserved
def test_question_is_preserved(sample_profile: Any) -> None:
    question_text = "Compare category revenue totals."
    generator = GeminiPythonCodeGenerator(llm=FakeBaseLLM())
    req = generator.generate(question_text, schema=sample_profile)

    assert req.question == question_text


# 4. Dataset hash is preserved
def test_dataset_hash_is_preserved(sample_profile: Any) -> None:
    hash_val = "sha256_mock_hash_123"
    generator = GeminiPythonCodeGenerator(llm=FakeBaseLLM())
    req = generator.generate("Avg price?", schema=sample_profile, dataset_hash=hash_val)

    assert req.dataset_hash == hash_val


# 5. Expected artifact type is preserved
def test_expected_artifact_type_is_preserved(sample_profile: Any) -> None:
    program = GeneratedPythonProgram(
        code="result = 42.0",
        explanation="Scalar output",
        expected_output_type=PythonArtifactType.SCALAR,
    )
    generator = GeminiPythonCodeGenerator(llm=FakeBaseLLM(program))
    req = generator.generate("Total?", schema=sample_profile)

    assert req.metadata["expected_output_type"] == "scalar"


# 6. Confidence is preserved
def test_confidence_is_preserved(sample_profile: Any) -> None:
    program = GeneratedPythonProgram(
        code="result = 10",
        explanation="High confidence",
        confidence=0.99,
    )
    generator = GeminiPythonCodeGenerator(llm=FakeBaseLLM(program))
    req = generator.generate("Test question", schema=sample_profile)

    assert req.metadata["confidence"] == 0.99


# 7. Retrieved columns are included in prompt context
def test_retrieved_columns_included_in_context(sample_profile: Any) -> None:
    fake_llm = FakeBaseLLM()
    generator = GeminiPythonCodeGenerator(llm=fake_llm)
    generator.generate(
        "Revenue analysis",
        schema=sample_profile,
        retrieved_columns=["revenue", "quantity"],
    )

    prompt_str = str(fake_llm.last_input)
    assert "revenue" in prompt_str
    assert "quantity" in prompt_str


# 8. Schema is included in prompt context
def test_schema_included_in_context(sample_profile: Any) -> None:
    fake_llm = FakeBaseLLM()
    generator = GeminiPythonCodeGenerator(llm=fake_llm)
    generator.generate("Schema check", schema=sample_profile)

    prompt_str = str(fake_llm.last_input)
    assert "unit_price" in prompt_str
    assert "category" in prompt_str


# 9. Empty question is rejected
def test_empty_question_rejected(sample_profile: Any) -> None:
    generator = GeminiPythonCodeGenerator(llm=FakeBaseLLM())
    with pytest.raises(PythonCodeGenerationError, match="must not be empty"):
        generator.generate("", schema=sample_profile)


# 10. Malformed structured output is rejected
def test_malformed_structured_output_rejected(sample_profile: Any) -> None:
    mock_llm = MagicMock(spec=BaseLLM)
    mock_llm.model_name = "mock-llm"
    mock_llm.invoke.return_value = AIMessage(content="INVALID_NON_JSON_STRING")

    generator = GeminiPythonCodeGenerator(llm=mock_llm)
    with pytest.raises(PythonCodeGenerationError, match="Failed to generate structured Python"):
        generator.generate("Test query", schema=sample_profile)


# 11. Unknown columns are rejected where validation is applicable
def test_unknown_columns_rejected(sample_profile: Any) -> None:
    invalid_program = GeneratedPythonProgram(
        code="result = df['non_existent_column'].sum()",
        explanation="Used invalid column",
        referenced_columns=["non_existent_column"],
    )
    generator = GeminiPythonCodeGenerator(llm=FakeBaseLLM(invalid_program))
    with pytest.raises(PythonCodeGenerationError, match="unknown column 'non_existent_column'"):
        generator.generate("Test invalid col", schema=sample_profile)


# 12. No execution occurs inside generator
def test_no_execution_occurs_inside_generator(sample_profile: Any) -> None:
    program = GeneratedPythonProgram(
        code="result = df['revenue'].mean()",
        explanation="Mean calculation",
    )
    generator = GeminiPythonCodeGenerator(llm=FakeBaseLLM(program))
    req = generator.generate("Test exec isolation", schema=sample_profile)

    # Assert request object returned without executing code or creating output artifacts
    assert isinstance(req, PythonExecutionRequest)
    assert not hasattr(req, "artifacts")


# 13. Generator module does not import subprocess or docker
def test_generator_module_imports() -> None:
    import csv_analytics_agent.llm.python_generator as gen_module

    mod_source = Path(gen_module.__file__).read_text(encoding="utf-8")
    assert "import subprocess" not in mod_source
    assert "import docker" not in mod_source


# 14. Generator does not call exec() or eval()
def test_generator_does_not_call_exec_or_eval() -> None:
    import csv_analytics_agent.llm.python_generator as gen_module

    tree = ast.parse(Path(gen_module.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in ("exec", "eval", "compile")


# 15. Metadata is generated correctly
def test_metadata_generated_correctly(sample_profile: Any) -> None:
    program = GeneratedPythonProgram(
        code="result = 100",
        explanation="Test explanation",
        expected_output_type=PythonArtifactType.SCALAR,
        confidence=0.88,
    )
    fake_llm = FakeBaseLLM(program)
    generator = GeminiPythonCodeGenerator(llm=fake_llm)
    req = generator.generate("Query", schema=sample_profile)

    assert req.metadata["generator"] == "gemini"
    assert req.metadata["model"] == "fake-gemini-model"
    assert req.metadata["expected_output_type"] == "scalar"
    assert req.metadata["confidence"] == 0.88
    assert req.metadata["explanation"] == "Test explanation"


# Golden Regression Cases Test
def test_golden_prompt_regression_cases(sample_profile: Any) -> None:
    fixture_path = Path(__file__).parent.parent / "fixtures" / "python_generation_cases.json"
    assert fixture_path.exists()

    cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    for case in cases:
        program = GeneratedPythonProgram(
            code=f"result = {case['expected_code_snippet']}",
            explanation=f"Generated for {case['id']}",
            expected_output_type=PythonArtifactType(case["allowed_output_types"][0]),
            referenced_columns=case["required_columns"],
        )
        generator = GeminiPythonCodeGenerator(llm=FakeBaseLLM(program))
        req = generator.generate(case["question"], schema=sample_profile)

        assert req.question == case["question"]
        assert req.metadata["expected_output_type"] in case["allowed_output_types"]
        schema_col_names = {c.name for c in sample_profile.columns}
        for col in case["required_columns"]:
            assert col in schema_col_names


# Live LLM Smoke Test
@pytest.mark.llm
def test_live_gemini_python_generator_smoke(sample_profile: Any) -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("GOOGLE_API_KEY environment variable not set.")

    llm = GeminiLLM()
    generator = GeminiPythonCodeGenerator(llm=llm)
    req = generator.generate(
        "What is the total revenue?",
        schema=sample_profile,
        retrieved_columns=["revenue"],
    )

    assert isinstance(req, PythonExecutionRequest)
    assert req.code != ""
    assert "revenue" in req.code or "result" in req.code
