"""CSV data loader for csv_analytics_agent."""

from io import BytesIO
from pathlib import Path

import pandas as pd

from csv_analytics_agent.config import Settings, get_settings
from csv_analytics_agent.data.validator import FileValidator
from csv_analytics_agent.exceptions import (
    CSVEncodingError,
    CSVParsingError,
    EmptyCSVError,
)
from csv_analytics_agent.logging_config import get_logger

logger = get_logger(__name__)


class CSVLoader:
    """Load validated CSV file into pandas DataFrame."""

    def __init__(
        self,
        validator: FileValidator | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._validator = validator or FileValidator(settings=self._settings)

    @classmethod
    def load_from_bytes(cls, data: bytes, filename: str) -> pd.DataFrame:
        """Load CSV data from bytes into a pandas DataFrame."""
        loader = cls()
        logger.info("csv_bytes_load_start", filename=filename, size_bytes=len(data))
        try:
            df = pd.read_csv(
                BytesIO(data),
                encoding=loader._settings.default_encoding,
            )
            if df.empty:
                raise EmptyCSVError(f"CSV stream '{filename}' is empty")
            logger.info(
                "csv_bytes_load_success",
                filename=filename,
                rows=len(df),
                columns=len(df.columns),
            )
            return df
        except pd.errors.EmptyDataError as err:
            logger.error("csv_bytes_load_failed", filename=filename, error_type="EmptyDataError")
            raise EmptyCSVError(f"CSV stream '{filename}' contains no data") from err
        except UnicodeError as err:
            logger.error(
                "csv_bytes_load_failed",
                filename=filename,
                error_type="CSVEncodingError",
                encoding=loader._settings.default_encoding,
            )
            raise CSVEncodingError(
                f"Failed to decode CSV stream '{filename}' using encoding "
                f"'{loader._settings.default_encoding}': {err}"
            ) from err
        except pd.errors.ParserError as err:
            logger.error("csv_bytes_load_failed", filename=filename, error_type="CSVParsingError")
            raise CSVParsingError(f"Failed to parse CSV stream '{filename}': {err}") from err
        except Exception as err:
            if isinstance(err, (EmptyCSVError, CSVEncodingError, CSVParsingError)):
                raise
            logger.error(
                "csv_bytes_load_failed",
                filename=filename,
                error_type=type(err).__name__,
            )
            raise CSVParsingError(
                f"Unexpected error loading CSV stream '{filename}': {err}"
            ) from err

    def load(self, path: Path) -> pd.DataFrame:
        """Load a validated CSV file into a pandas DataFrame.

        Args:
            path: Path to the CSV file to load.

        Returns:
            pandas.DataFrame containing the loaded CSV data.

        Raises:
            FileValidationError: If file validation fails.
            EmptyCSVError: If the CSV file is empty.
            CSVEncodingError: If decoding the file fails with configured encoding.
            CSVParsingError: If pandas fails to parse the CSV structure.
        """
        self._validator.validate(path)

        try:
            df = pd.read_csv(
                path,
                encoding=self._settings.default_encoding,
            )
            if df.empty:
                raise EmptyCSVError(f"CSV file is empty: {path}")
            return df
        except pd.errors.EmptyDataError as err:
            raise EmptyCSVError(f"CSV file contains no data: {path}") from err
        except UnicodeError as err:
            raise CSVEncodingError(
                f"Failed to decode CSV file '{path}' using encoding "
                f"'{self._settings.default_encoding}': {err}"
            ) from err
        except pd.errors.ParserError as err:
            raise CSVParsingError(f"Failed to parse CSV file '{path}': {err}") from err
        except (EmptyCSVError, CSVEncodingError, CSVParsingError):
            raise
        except Exception as err:
            raise CSVParsingError(f"Unexpected error loading CSV file '{path}': {err}") from err
