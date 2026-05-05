import csv
import logging
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

LOGGER_NAME = "tiqets_assignment"


class ValidationError(Exception):
    """Exception raised for validation errors in CSV processing."""
    pass


def configure_logger() -> logging.Logger:
    """Configure and return a logger for the application.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def parse_csv_header(reader: csv.DictReader, expected_fields: List[str]) -> None:
    """Parse and validate the CSV header.

    Args:
        reader: CSV DictReader instance.
        expected_fields: List of expected field names.

    Raises:
        ValidationError: If header is missing or doesn't match expected fields.
    """
    if reader.fieldnames is None:
        raise ValidationError("CSV file is missing a header row")
    header = [field.strip() for field in reader.fieldnames]
    if header != expected_fields:
        raise ValidationError(
            f"Expected header {expected_fields!r}, found {header!r}"
        )


def iter_csv_rows(path: Path, expected_fields: List[str]) -> Iterator[Tuple[int, Dict[str, str]]]:
    """Iterate over CSV rows with validation.

    Args:
        path: Path to the CSV file.
        expected_fields: List of expected field names.

    Yields:
        Tuple of (row_index, row_dict) for each row.

    Raises:
        ValidationError: If header validation fails.
    """
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        parse_csv_header(reader, expected_fields)
        for row_index, row in enumerate(reader, start=2):
            yield row_index, {key: (value or "").strip() for key, value in row.items()}
