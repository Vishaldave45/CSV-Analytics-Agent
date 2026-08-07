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

    checkpoint_path: Path = Field(
        default=Path("sessions.db"),
        description="SQLite database path for conversation state checkpointing.",
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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
