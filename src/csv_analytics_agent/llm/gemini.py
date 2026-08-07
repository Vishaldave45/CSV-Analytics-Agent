"""Gemini LLM provider implementation using ChatGoogleGenerativeAI."""

from __future__ import annotations

import os
from typing import Any, cast

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from csv_analytics_agent.llm.base import BaseLLM


class GeminiLLM(BaseLLM):
    """Google Gemini LLM wrapper implementing BaseLLM interface."""

    def __init__(
        self,
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.0,
        api_key: str | None = None,
        llm_instance: Any | None = None,
    ) -> None:
        """Initialize GeminiLLM instance.

        Args:
            model_name: Gemini model string identifier (default 'gemini-1.5-flash').
            temperature: Sampling temperature float (default 0.0).
            api_key: Optional Google API key string.
            llm_instance: Optional pre-configured Runnable/Chat model for injection/testing.
        """
        self._model_name = model_name
        self._temperature = temperature
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if llm_instance is not None:
            self._llm = llm_instance
        else:
            self._llm = ChatGoogleGenerativeAI(
                model=self._model_name,
                temperature=self._temperature,
                google_api_key=self._api_key or "DUMMY_KEY_FOR_MOCKING",
            )

    def bind_tools(self, tools: list[Any]) -> BaseLLM:
        """Bind tools to Gemini Chat model and return new GeminiLLM instance.

        Args:
            tools: List of StructuredTool instances.

        Returns:
            New GeminiLLM wrapping bound model.
        """
        bound_llm = self._llm.bind_tools(tools)
        return GeminiLLM(
            model_name=self._model_name,
            temperature=self._temperature,
            api_key=self._api_key,
            llm_instance=bound_llm,
        )

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        """Invoke Gemini LLM with messages or prompt input.

        Args:
            input_data: Conversation messages list or prompt string.

        Returns:
            BaseMessage response emitted by ChatGoogleGenerativeAI.
        """
        response = self._llm.invoke(cast(Any, input_data))
        return cast(BaseMessage, response)

    def stream(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> Any:
        """Stream token response chunks from Gemini LLM.

        Args:
            input_data: Input message history or prompt text.

        Returns:
            Iterator of response chunks.
        """
        return self._llm.stream(cast(Any, input_data))

    @property
    def model_name(self) -> str:
        return self._model_name


__all__ = ["GeminiLLM"]
