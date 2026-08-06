from pathlib import Path

import pytest

from csv_analytics_agent.config import Settings
from csv_analytics_agent.data.validator import FileValidator
from csv_analytics_agent.exceptions import (
    FileValidationError,
    InvalidFileExtensionError,
)


def test_validator_valid_file(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("a,b,c\n1,2,3")

    validator = FileValidator()
    # Should not raise any error
    validator.validate(csv_file)


def test_validator_file_does_not_exist(tmp_path: Path) -> None:
    non_existent = tmp_path / "missing.csv"

    validator = FileValidator()
    with pytest.raises(FileValidationError, match="File does not exist"):
        validator.validate(non_existent)


def test_validator_path_is_directory(tmp_path: Path) -> None:
    validator = FileValidator()
    with pytest.raises(FileValidationError, match="Path is not a regular file"):
        validator.validate(tmp_path)


def test_validator_invalid_extension(tmp_path: Path) -> None:
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("some text")

    validator = FileValidator()
    with pytest.raises(InvalidFileExtensionError):
        validator.validate(txt_file)


def test_validator_file_too_large(tmp_path: Path) -> None:
    csv_file = tmp_path / "large.csv"
    # Write ~2 MB file
    csv_file.write_text("x" * (2 * 1024 * 1024))

    custom_settings = Settings(max_csv_size_mb=1)
    validator = FileValidator(settings=custom_settings)

    with pytest.raises(FileValidationError, match="exceeds maximum limit"):
        validator.validate(csv_file)
