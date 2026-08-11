"""Application Settings module using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings for CSV Analytics Agent and Graph Runtime."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    default_encoding: str = Field(
        default="utf-8",
        description="Default CSV encoding.",
    )

    supported_extensions: tuple[str, ...] = (".csv",)

    output_directory: Path = Path("outputs")

    max_csv_size_mb: int = Field(
        default=500,
        ge=1,
        description="Maximum allowed CSV size in MB.",
    )

    max_iterations: int = Field(
        default=6,
        ge=1,
        description="Maximum loop iteration limit for LLM planner node.",
    )

    default_thread_id: str = Field(
        default="default_thread",
        description="Default thread identifier for graph checkpointing.",
    )

    gemini_rpm: int = Field(
        default=10,
        ge=1,
        description="Gemini API rate limit: maximum requests per minute (free tier).",
    )

    google_api_key: str | None = Field(
        default=None,
        description="Google AI Studio API key (read from GOOGLE_API_KEY env var).",
    )

    python_execution_backend: str = Field(
        default="subprocess",
        description="Python execution backend choice ('subprocess' or 'container').",
    )

    python_sandbox_image: str = Field(
        default="csv-analytics-python:latest",
        description="Docker image name for containerized Python execution.",
    )

    python_sandbox_memory_mb: int = Field(
        default=512,
        ge=1,
        description="Memory limit in MB for Python sandbox.",
    )

    python_sandbox_cpu_limit: float = Field(
        default=1.0,
        gt=0.0,
        description="CPU core count limit for Python sandbox.",
    )

    python_sandbox_pids_limit: int = Field(
        default=64,
        ge=1,
        description="Maximum process PID count limit for Python sandbox.",
    )

    python_sandbox_timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Timeout limit in seconds for Python execution.",
    )

    python_sandbox_network: bool = Field(
        default=False,
        description="Whether network access is permitted in Python sandbox.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
