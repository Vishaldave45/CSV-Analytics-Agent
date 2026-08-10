"""Observability configuration module for LangSmith tracing."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ObservabilitySettings(BaseSettings):
    """Configuration settings for LangSmith tracing, logging, and metrics."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    tracing_v2: bool = Field(
        default=False,
        validation_alias="LANGSMITH_TRACING",
        description="Enable or disable LangSmith tracing.",
    )

    api_key: str | None = Field(
        default=None,
        validation_alias="LANGSMITH_API_KEY",
        description="LangSmith API key for metric upload.",
    )

    project: str = Field(
        default="csv-analytics-agent",
        validation_alias="LANGSMITH_PROJECT",
        description="LangSmith project identifier.",
    )

    endpoint: str = Field(
        default="https://api.smith.langchain.com",
        validation_alias="LANGSMITH_ENDPOINT",
        description="LangSmith endpoint URL.",
    )

    session: str = Field(
        default="development",
        alias="LANGCHAIN_SESSION",
        description="LangSmith session tag or environment mode.",
    )

    # Store as raw comma-separated string to avoid pydantic-settings JSON-parsing
    # a plain "local,csv-agent" value from .env as complex type.
    tags_raw: str = Field(
        default="local,csv-agent",
        alias="LANGCHAIN_TAGS",
        description="Comma-separated global tags attached to all traced runs.",
    )

    metadata: dict[str, str] = Field(
        default_factory=dict,
        alias="LANGCHAIN_METADATA",
        description="Global metadata payload for traced runs.",
    )

    @property
    def tags(self) -> list[str]:
        """Return parsed list of tags from comma-separated raw string."""
        return [t.strip() for t in self.tags_raw.split(",") if t.strip()]


@lru_cache(maxsize=1)
def get_observability_settings() -> ObservabilitySettings:
    """Return a cached ObservabilitySettings instance."""
    return ObservabilitySettings()


__all__ = ["ObservabilitySettings", "get_observability_settings"]
