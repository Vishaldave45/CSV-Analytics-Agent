"""Abstract BaseLLM interface for language model providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import BaseMessage


class BaseLLM(ABC):
    """Abstract interface defining the language model contract for graph nodes."""

    @abstractmethod
    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        """Bind LangChain tools to the LLM instance.

        Args:
            tools: List of LangChain StructuredTool or tool schema objects.

        Returns:
            Bound BaseLLM instance ready for tool call invocation.
        """
        ...

    @abstractmethod
    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        """Invoke the LLM with message history or prompt text.

        Args:
            input_data: Conversation messages, string prompt, or payload dict.

        Returns:
            BaseMessage response emitted by the LLM (e.g. AIMessage with tool_calls).
        """
        ...

    @abstractmethod
    def stream(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> Any:
        """Stream token chunks from the LLM response.

        Args:
            input_data: Input message history or prompt text.

        Returns:
            Iterator or AsyncIterator of response chunks.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the programmatic model identifier string."""
        ...


__all__ = ["BaseLLM"]
