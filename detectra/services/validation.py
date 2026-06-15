"""Validation helpers for uploaded spectrum files."""

from pathlib import Path

import pandas as pd


REQUIRED_SPECTRUM_COLUMNS = ("wavenumber", "absorbance")
MINIMUM_SPECTRUM_ROWS = 10


def allowed_file(filename: str) -> bool:
    """Return whether an uploaded filename has the supported CSV extension."""
    return Path(filename).suffix.lower() == ".csv"


def validate_csv_format(filepath: str | Path) -> tuple[bool, str]:
    """Validate the required columns and minimum row count of a spectrum CSV."""
    try:
        dataframe = pd.read_csv(filepath)
    except Exception as exc:
        return False, f"Error reading CSV: {exc}"

    missing_columns = [
        column
        for column in REQUIRED_SPECTRUM_COLUMNS
        if column not in dataframe.columns
    ]
    if missing_columns:
        required = ", ".join(REQUIRED_SPECTRUM_COLUMNS)
        return False, f"CSV must contain columns: {required}"

    if len(dataframe) < MINIMUM_SPECTRUM_ROWS:
        return False, f"CSV must contain at least {MINIMUM_SPECTRUM_ROWS} data points"

    return True, "Valid CSV format"
