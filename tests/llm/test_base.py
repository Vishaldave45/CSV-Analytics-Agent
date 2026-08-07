"""Unit tests for BaseLLM abstraction."""

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage

from csv_analytics_agent.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """Concrete mock implementation of BaseLLM for testing."""

    def __init__(self, model_name: str = "mock_model") -> None:
        self._model_name = model_name
        self.bound_tools: list[Any] = []

    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        new_llm = MockLLM(self._model_name)
        new_llm.bound_tools = tools
        return new_llm

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        return AIMessage(content="Mock LLM response")

    def stream(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> Any:
        yield AIMessage(content="Mock stream chunk")

    @property
    def model_name(self) -> str:
        return self._model_name


def test_base_llm_interface() -> None:
    llm = MockLLM()
    assert llm.model_name == "mock_model"

    bound = llm.bind_tools(["tool_a", "tool_b"])
    assert isinstance(bound, BaseLLM)
    assert getattr(bound, "bound_tools", []) == ["tool_a", "tool_b"]

    res = bound.invoke("Hello")
    assert isinstance(res, AIMessage)
    assert res.content == "Mock LLM response"
