"""Unit tests for ObservabilitySettings configuration."""

from csv_analytics_agent.observability.config import (
    ObservabilitySettings,
    get_observability_settings,
)


def test_observability_settings_defaults() -> None:
    """Verify default observability settings values."""
    settings = ObservabilitySettings()
    assert settings.tracing_v2 is False
    assert settings.project == "csv-analytics-agent"
    assert settings.endpoint == "https://api.smith.langchain.com"
    assert "local" in settings.tags


def test_get_observability_settings_cached() -> None:
    """Verify get_observability_settings returns a valid settings instance."""
    settings = get_observability_settings()
    assert isinstance(settings, ObservabilitySettings)
