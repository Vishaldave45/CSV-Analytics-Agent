"""File validator for csv_analytics_agent."""

from pathlib import Path

from csv_analytics_agent.config import Settings, get_settings
from csv_analytics_agent.exceptions import (
    FileValidationError,
    InvalidFileExtensionError,
)


class FileValidator:
    """Validate input file before loading."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def validate(self, path: Path) -> None:
        """Validate an input file path.

        Args:
            path: Path to the input file to validate.

        Raises:
            FileValidationError: If the file does not exist, is not a regular file,
                or exceeds maximum allowed size.
            InvalidFileExtensionError: If the file extension is not supported.
        """
        if not path.exists():
            raise FileValidationError(f"File does not exist: {path}")

        if not path.is_file():
            raise FileValidationError(f"Path is not a regular file: {path}")

        if path.suffix.lower() not in self._settings.supported_extensions:
            raise InvalidFileExtensionError(
                file_path=str(path),
                allowed_extensions=self._settings.supported_extensions,
            )

        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self._settings.max_csv_size_mb:
            raise FileValidationError(
                f"File size ({file_size_mb:.2f} MB) exceeds maximum limit "
                f"of {self._settings.max_csv_size_mb} MB."
            )
