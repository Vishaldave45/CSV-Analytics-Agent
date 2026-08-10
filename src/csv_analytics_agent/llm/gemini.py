"""Gemini LLM provider implementation using ChatGoogleGenerativeAI."""

from __future__ import annotations

import logging
import os
from typing import Any, cast

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.logging_config import get_logger

logger = get_logger(__name__)
_stdlib_log = logging.getLogger(__name__)

# Collect all available transient error types across SDKs (google-genai, google-api-core, httpx)
_transient_list: list[type[Exception]] = []

try:
    from google.api_core.exceptions import (  # pyright: ignore[reportMissingImports]
        ResourceExhausted,
        ServiceUnavailable,
    )

    _transient_list.extend([ResourceExhausted, ServiceUnavailable])
except (ImportError, ModuleNotFoundError):
    pass

try:
    from google.genai.errors import (  # pyright: ignore[reportMissingImports]
        APIError,
        ServerError,
    )

    _transient_list.extend([APIError, ServerError])
except (ImportError, ModuleNotFoundError):
    pass

try:
    import httpx  # pyright: ignore[reportMissingImports]

    _transient_list.extend([httpx.ConnectError, httpx.TimeoutException])
except (ImportError, ModuleNotFoundError):
    pass

_TRANSIENT_EXCEPTIONS: tuple[type[Exception], ...] = tuple(_transient_list)


def _log_retry(retry_state: RetryCallState) -> None:
    """Log retry attempt with structured context before sleeping."""
    attempt = retry_state.attempt_number
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "gemini_retry",
        attempt=attempt,
        error_type=type(exc).__name__ if exc else "unknown",
        error=str(exc) if exc else "",
    )


_retry_predicate = (
    retry_if_exception_type(_TRANSIENT_EXCEPTIONS)
    if _TRANSIENT_EXCEPTIONS
    else retry_if_exception_type(())
)


class GeminiLLM(BaseLLM):
    """Google Gemini LLM wrapper implementing BaseLLM interface."""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.0,
        api_key: str | None = None,
        llm_instance: Any | None = None,
        limiter: Any | None = None,
    ) -> None:
        """Initialize GeminiLLM instance.

        Args:
            model_name: Gemini model string identifier (default 'gemini-2.5-flash').
            temperature: Sampling temperature float (default 0.0).
            api_key: Optional Google API key string.
            llm_instance: Optional pre-configured Runnable/Chat model for injection/testing.
            limiter: Optional pyrate_limiter.Limiter instance for rate limiting.
        """
        formatted_model = model_name.strip().replace(" ", "-") if model_name else "gemini-2.5-flash"
        self._model_name = formatted_model
        self._temperature = temperature
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._limiter = limiter

        if llm_instance is not None:
            self._llm = llm_instance
        else:
            self._llm = ChatGoogleGenerativeAI(
                model=self._model_name,
                temperature=self._temperature,
                google_api_key=self._api_key or "DUMMY_KEY_FOR_MOCKING",
            )

    # ---------------------------------------------------------------------------
    # Private: retryable inner call — only wraps the transient-error cases
    # ---------------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=_retry_predicate,
        before_sleep=_log_retry,
        reraise=True,
    )
    def _invoke_inner(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        """Internal invoke — wrapped by tenacity for retries on transient failures."""
        response = self._llm.invoke(cast(Any, input_data))
        return cast(BaseMessage, response)

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

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
            limiter=self._limiter,
        )

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        """Invoke Gemini LLM with messages or prompt input.

        Applies rate limiting (if a limiter is configured) before the call, then
        delegates to ``_invoke_inner`` which is wrapped with tenacity retry logic for
        transient errors (rate limits / service unavailability).

        Auth errors (``API_KEY_INVALID``, ``INVALID_ARGUMENT``) are caught here and
        converted to a ``ValueError`` with an actionable message — they are NOT retried.

        Args:
            input_data: Conversation messages list or prompt string.

        Returns:
            BaseMessage response emitted by ChatGoogleGenerativeAI.

        Raises:
            ValueError: If the API key is invalid or the argument is malformed.
        """
        # Rate limiting gate — blocks until a slot is available
        if self._limiter is not None:
            try:
                self._limiter.try_acquire("gemini_invoke")
            except Exception:  # noqa: BLE001
                # Limiter raised (raise_when_fail=True path) — treat as rate limit warning
                logger.warning("gemini_rate_limit_wait", model=self._model_name)

        try:
            return self._invoke_inner(input_data)
        except Exception as err:
            err_str = str(err)
            if "API_KEY_INVALID" in err_str or "INVALID_ARGUMENT" in err_str:
                raise ValueError(
                    "Invalid Google Gemini API Key. "
                    "Please check your key at https://aistudio.google.com/app/apikey "
                    "and enter it in Settings."
                ) from err
            raise

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
