"""Unit tests for normalize_message_content and message handling regression tests."""

from typing import Any
from unittest.mock import MagicMock

import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage

from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.build import build_graph
from csv_analytics_agent.graph.message_utils import (
    extract_last_human_text,
    normalize_message_content,
)
from csv_analytics_agent.llm.base import BaseLLM


def test_normalize_message_content_plain_string() -> None:
    """Verify normalize_message_content with plain string input."""
    assert normalize_message_content("hello") == "hello"
    assert normalize_message_content("  hello world  ") == "hello world"


def test_normalize_message_content_structured_text_blocks() -> None:
    """Verify normalize_message_content with structured list of dict blocks."""
    blocks = [{"type": "text", "text": "hello"}]
    assert normalize_message_content(blocks) == "hello"

    multi_blocks = [
        {"type": "text", "text": "hello "},
        {"type": "text", "text": "world"},
    ]
    assert normalize_message_content(multi_blocks) == "hello world"


def test_normalize_message_content_string_list() -> None:
    """Verify normalize_message_content with list of strings."""
    assert normalize_message_content(["hello", "world"]) == "hello world"


def test_normalize_message_content_none_and_empty() -> None:
    """Verify normalize_message_content with None and empty values."""
    assert normalize_message_content(None) == ""
    assert normalize_message_content("") == ""
    assert normalize_message_content([]) == ""


def test_extract_last_human_text_with_structured_content() -> None:
    """Verify extract_last_human_text extracts text from HumanMessage with list content."""
    msg = HumanMessage(content=[{"type": "text", "text": "hii"}])
    assert extract_last_human_text([msg]) == "hii"


class ListContentFakeLLM(BaseLLM):
    """Fake LLM returning AIMessage with list content blocks."""

    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        return self

    def invoke(self, input_data: Any) -> AIMessage:
        # Simulate LLMs returning list content blocks (multimodal/anthropic/gemini format)
        return AIMessage(content=[{"type": "text", "text": "Analysis overview."}])

    def stream(self, input_data: Any) -> Any:
        yield self.invoke(input_data)

    @property
    def model_name(self) -> str:
        return "list-content-fake-llm"


def test_regression_hii_query_with_list_content() -> None:
    """Regression test verifying 'hii' query with list message content does not raise AttributeError."""
    df = pd.DataFrame({"category": ["A", "B"], "sales": [10, 20]})
    registry = CapabilityRegistry()
    mem_service = MagicMock()
    fake_llm = ListContentFakeLLM()

    graph = build_graph(
        llm=fake_llm,
        registry=registry,
        memory_service=mem_service,
        dataframe=df,
    )

    initial_state = {
        "messages": [HumanMessage(content=[{"type": "text", "text": "hii"}])],
    }

    # Graph invocation must complete cleanly without raising AttributeError: 'list' object has no attribute 'strip'
    result_state = graph.invoke(initial_state)

    assert "messages" in result_state
    last_msg = result_state["messages"][-1]
    assert normalize_message_content(last_msg.content) != ""
