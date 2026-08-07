class CSVAnalyticsError(Exception):
    """Base exception for all csv-analytics-agent exceptions."""

    pass


class DataLoaderError(CSVAnalyticsError):
    """Base exception for errors encountered while loading or validating data."""

    pass


class InvalidFileExtensionError(DataLoaderError, ValueError):
    """Raised when a file extension is not supported (e.g., non-.csv files)."""

    def __init__(
        self,
        message: str = "Invalid file extension provided.",
        file_path: str | None = None,
        allowed_extensions: tuple[str, ...] | None = None,
    ) -> None:
        self.file_path = file_path
        self.allowed_extensions = allowed_extensions
        if file_path and allowed_extensions:
            message = (
                f"File '{file_path}' has an invalid extension. "
                f"Allowed extensions: {allowed_extensions}"
            )
        super().__init__(message)


class FileValidationError(DataLoaderError, ValueError):
    """Raised when file validation fails (e.g. file size exceeds maximum limits)."""

    pass


class EmptyCSVError(DataLoaderError, ValueError):
    """Raised when the loaded CSV file is empty."""

    pass


class CSVParsingError(DataLoaderError, ValueError):
    """Raised when error occurs during CSV parsing."""

    pass


class CSVEncodingError(DataLoaderError, UnicodeError):
    """Raised when decoding/encoding issues occur while reading CSV files."""

    pass
