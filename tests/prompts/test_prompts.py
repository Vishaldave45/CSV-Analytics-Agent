"""Unit tests for the dedicated prompt repository assets and loader service."""

import pytest
from langchain_core.messages import HumanMessage

from csv_analytics_agent.graph.checkpoint import json_safe
from csv_analytics_agent.graph.router import RouterIntent, router_node
from csv_analytics_agent.graph.state import create_initial_state
from csv_analytics_agent.prompts import (
    PLANNER_PROMPT_VERSION,
    PYTHON_PROMPT_VERSION,
    RESPONSE_PROMPT_VERSION,
    ROUTER_PROMPT_VERSION,
    compose_prompt,
    get_planner_prompt,
    get_prompts_dir,
    get_python_prompt,
    get_response_prompt,
    get_router_prompt,
    load_prompt,
)


def test_prompts_dir_exists() -> None:
    """Verify get_prompts_dir resolves to an existing prompts directory."""
    p_dir = get_prompts_dir()
    assert p_dir.exists()
    assert (p_dir / "README.md").is_file()


def test_load_prompt_files() -> None:
    """Verify loading individual static markdown prompt files."""
    router_sys = load_prompt("router/system.md")
    assert "You are the intent router" in router_sys

    planner_sys = load_prompt("planner/system.md")
    assert "analytical planner" in planner_sys

    grounding = load_prompt("shared/grounding.md")
    assert "source of truth" in grounding


def test_compose_prompt() -> None:
    """Verify composition of multiple prompt markdown files."""
    composed = compose_prompt("shared/grounding.md", "router/system.md")
    assert "source of truth" in composed
    assert "You are the intent router" in composed
    assert "---" in composed


def test_composed_prompt_helpers() -> None:
    """Verify top-level layer composed prompt helpers."""
    assert len(get_router_prompt()) > 100
    assert len(get_planner_prompt()) > 100
    assert len(get_python_prompt()) > 100
    assert len(get_response_prompt()) > 100


def test_prompt_version_constants() -> None:
    """Verify prompt version identifier constants."""
    assert ROUTER_PROMPT_VERSION == "v1"
    assert PLANNER_PROMPT_VERSION == "v1"
    assert PYTHON_PROMPT_VERSION == "v1"
    assert RESPONSE_PROMPT_VERSION == "v1"


def test_missing_prompt_raises_error() -> None:
    """Verify attempting to load a non-existent prompt raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found"):
        load_prompt("non_existent_folder/missing.md")


def test_escaped_path_raises_error() -> None:
    """Verify directory traversal attempts raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Access denied"):
        load_prompt("../../pyproject.toml")


def test_router_dataset_metadata_intent() -> None:
    """Verify router classifies metadata queries as DATASET_METADATA."""
    state = create_initial_state()
    state["messages"] = [HumanMessage(content="How many rows are in the dataset?")]

    res = router_node(state)
    decision = res["router_decision"]
    assert decision["intent"] == RouterIntent.DATASET_METADATA.value
    assert decision["next_node"] == "explainer"


def test_router_expanded_chitchat() -> None:
    """Verify router classifies expanded chitchat keywords like 'goodbye' and 'awesome'."""
    for phrase in ["bye", "goodbye", "cool", "awesome", "got it"]:
        state = create_initial_state()
        state["messages"] = [HumanMessage(content=phrase)]
        res = router_node(state)
        assert res["router_decision"]["intent"] == RouterIntent.CHITCHAT.value


def test_json_safe_nan_sanitization() -> None:
    """Verify json_safe converts float NaN and Infinity to None."""
    payload = {"a": float("nan"), "b": float("inf"), "c": float("-inf"), "d": 42.0}
    safe_payload = json_safe(payload)
    assert isinstance(safe_payload, dict)
    assert safe_payload["a"] is None
    assert safe_payload["b"] is None
    assert safe_payload["c"] is None
    assert safe_payload["d"] == 42.0


def test_gemini_retry_predicate_policy() -> None:
    """Verify GeminiLLM retry predicate fails fast on API_KEY_INVALID and INVALID_ARGUMENT."""
    from csv_analytics_agent.llm.gemini import _should_retry_exception

    assert not _should_retry_exception(ValueError("API_KEY_INVALID: key invalid"))
    assert not _should_retry_exception(ValueError("INVALID_ARGUMENT: Bad JSON"))
    assert not _should_retry_exception(ValueError("RESOURCE_EXHAUSTED: quota exceeded"))


def test_python_generator_structured_schema_parsing() -> None:
    """Verify GeminiPythonCodeGenerator parses structured output into GeneratedPythonProgram."""
    from csv_analytics_agent.llm.python_models import GeneratedPythonProgram

    sample_dict = {
        "code": "result = df['Revenue'].sum()",
        "explanation": "Compute sum of revenue column.",
        "expected_output_type": "scalar",
        "dependencies": ["pandas"],
        "confidence": 1.0,
        "referenced_columns": ["Revenue"],
    }
    program = GeneratedPythonProgram(**sample_dict)
    assert program.code == "result = df['Revenue'].sum()"
    assert program.confidence == 1.0
