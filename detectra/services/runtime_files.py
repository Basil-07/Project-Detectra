"""Lifecycle helpers for generated uploads, plots, and reports."""

import time
from pathlib import Path


def cleanup_old_files(
    folders,
    maximum_age_seconds: int = 3600,
) -> None:
    """Delete generated files older than the configured maximum age."""
    current_time = time.time()
    for folder in folders:
        for path in Path(folder).iterdir():
            if not path.is_file():
                continue
            if current_time - path.stat().st_ctime <= maximum_age_seconds:
                continue
            try:
                path.unlink()
            except OSError:
                pass
