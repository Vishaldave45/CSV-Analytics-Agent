"""CSV data loader for csv_analytics_agent."""

from pathlib import Path

import pandas as pd

from csv_analytics_agent.config import Settings, get_settings
from csv_analytics_agent.data.validator import FileValidator
from csv_analytics_agent.exceptions import (
    CSVEncodingError,
    CSVParsingError,
    EmptyCSVError,
)


class CSVLoader:
    """Load validated CSV file into pandas DataFrame."""

    def __init__(
        self,
        validator: FileValidator | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._validator = validator or FileValidator(settings=self._settings)

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
