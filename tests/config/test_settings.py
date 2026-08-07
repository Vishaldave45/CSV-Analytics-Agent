from csv_analytics_agent.config import get_settings


def test_default_encoding() -> None:
    settings = get_settings()

    assert settings.default_encoding == "utf-8"


def test_supported_extensions() -> None:
    settings = get_settings()

    assert ".csv" in settings.supported_extensions


def test_output_directory() -> None:
    settings = get_settings()

    assert settings.output_directory.name == "outputs"
