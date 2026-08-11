"""Gemini LLM provider implementation using ChatGoogleGenerativeAI."""

from __future__ import annotations

import os
import time
from typing import Any, cast

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from csv_analytics_agent.llm.base import BaseLLM
from csv_analytics_agent.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL_NAME = "gemini-flash-lite-latest"
AVAILABLE_MODELS = (
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-2.5-flash",
)

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


def _should_retry_exception(exception: BaseException) -> bool:
    err_str = str(exception)

    if "API_KEY_INVALID" in err_str or "INVALID_ARGUMENT" in err_str:
        return False
    if "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
        return False

    return isinstance(exception, _TRANSIENT_EXCEPTIONS)


_retry_predicate = retry_if_exception(_should_retry_exception)


class GeminiAPIKeyError(ValueError):
    """Exception raised when Google Gemini API key is missing or unconfigured."""

    pass


class GeminiLLM(BaseLLM):
    """Google Gemini LLM wrapper implementing BaseLLM interface."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        temperature: float = 0.0,
        api_key: str | None = None,
        llm_instance: Any | None = None,
        limiter: Any | None = None,
    ) -> None:
        """Initialize GeminiLLM instance.

        Args:
            model_name: Gemini model string identifier (default DEFAULT_MODEL_NAME).
            temperature: Sampling temperature float (default 0.0).
            api_key: Optional Google API key string.
            llm_instance: Optional pre-configured Runnable/Chat model for injection/testing.
            limiter: Optional pyrate_limiter.Limiter instance for rate limiting.
        """
        formatted_model = model_name.strip().replace(" ", "-") if model_name else DEFAULT_MODEL_NAME
        self._model_name = formatted_model
        self._temperature = temperature
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self._limiter = limiter
        self._owns_llm = llm_instance is None

        self._llm = llm_instance if llm_instance is not None else self._build_llm_instance()

    def _build_llm_instance(self) -> ChatGoogleGenerativeAI:
        if not self._api_key:
            raise GeminiAPIKeyError(
                "Google Gemini API Key is missing. "
                "Please set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )
        return ChatGoogleGenerativeAI(
            model=self._model_name,
            temperature=self._temperature,
            google_api_key=self._api_key,
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

    def _is_quota_error(self, error: Exception) -> bool:
        err_str = str(error)
        return "API_KEY_INVALID" not in err_str and (
            "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "quota" in err_str.lower()
        )

    def _get_fallback_model_name(self) -> str | None:
        return DEFAULT_MODEL_NAME if self._model_name != DEFAULT_MODEL_NAME else None

    def invoke(self, input_data: list[BaseMessage] | str | dict[str, Any]) -> BaseMessage:
        """Invoke Gemini LLM with messages or prompt input.

        Applies rate limiting (if a limiter is configured) before the call, then
        delegates to ``_invoke_inner`` which is wrapped with tenacity retry logic for
        transient errors.
        """
        if self._limiter is not None:
            try:
                self._limiter.try_acquire("gemini_invoke")
            except Exception:  # noqa: BLE001
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
            if self._is_quota_error(err):
                fallback_model = self._get_fallback_model_name()
                if fallback_model and self._owns_llm:
                    logger.warning(
                        "gemini_quota_fallback",
                        model=self._model_name,
                        fallback_model=fallback_model,
                    )
                    self._model_name = fallback_model
                    self._llm = self._build_llm_instance()
                    return self._invoke_inner(input_data)

                logger.warning("gemini_429_quota_waiting", model=self._model_name, wait_seconds=30)
                time.sleep(30.0)
                try:
                    return self._invoke_inner(input_data)
                except Exception as retry_err:
                    raise ValueError(
                        f"Gemini API Quota / Rate Limit Exceeded (429) for "
                        f"'{self._model_name}'. Try switching to "
                        f"'{DEFAULT_MODEL_NAME}' in Settings or wait 30-60s."
                    ) from retry_err
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
