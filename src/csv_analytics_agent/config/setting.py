from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    default_encoding: str = Field(
        default="utf-8",
        description="Default CSV encoding.",
    )
    
    supported_extensions: tuple[str, ...] = (
        ".csv",
    )
    
    output_directory: Path = Path("outputs")
    
    max_csv_size_mb: int = Field(
        default=500,
        ge=1,
        description="Maximum allowed CSV size in MB.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()