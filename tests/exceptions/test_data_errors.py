import pytest

from csv_analytics_agent.exceptions import (
    CSVAnalyticsError,
    CSVEncodingError,
    CSVParsingError,
    DataLoaderError,
    EmptyCSVError,
    FileValidationError,
    InvalidFileExtensionError,
)


def test_invalid_file_extension_error_default_message() -> None:
    err = InvalidFileExtensionError()
    assert str(err) == "Invalid file extension provided."
    assert isinstance(err, CSVAnalyticsError)
    assert isinstance(err, DataLoaderError)
    assert isinstance(err, ValueError)


def test_invalid_file_extension_error_custom_message() -> None:
    err = InvalidFileExtensionError(
        file_path="data.txt",
        allowed_extensions=(".csv",),
    )
    assert "data.txt" in str(err)
    assert "('.csv',)" in str(err)
    assert err.file_path == "data.txt"
    assert err.allowed_extensions == (".csv",)


def test_data_loader_exceptions() -> None:
    with pytest.raises(FileValidationError):
        raise FileValidationError("File size exceeds limit")

    with pytest.raises(EmptyCSVError):
        raise EmptyCSVError("CSV file is empty")

    with pytest.raises(CSVParsingError):
        raise CSVParsingError("Malformed CSV header")

    with pytest.raises(CSVEncodingError):
        raise CSVEncodingError("utf-8", b"\xff", 0, 1, "invalid start byte")
