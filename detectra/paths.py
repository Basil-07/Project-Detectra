"""Canonical filesystem paths used across Detectra."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "reference_spectra"
MODELS_DIR = PROJECT_ROOT / "models"
INSTANCE_DIR = PROJECT_ROOT / "instance"
UPLOADS_DIR = INSTANCE_DIR / "uploads"
REPORTS_DIR = INSTANCE_DIR / "reports"
PLOTS_DIR = INSTANCE_DIR / "plots"


def ensure_runtime_directories() -> None:
    """Create directories used for generated runtime files."""
    for directory in (UPLOADS_DIR, REPORTS_DIR, PLOTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
