"""Canonical filesystem paths used across Detectra."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "reference_spectra"
IS_VERCEL = bool(os.getenv("VERCEL"))
INSTANCE_DIR = (
    Path(os.getenv("DETECTRA_RUNTIME_DIR", "/tmp/detectra"))
    if IS_VERCEL
    else PROJECT_ROOT / "instance"
)
MODELS_DIR = (
    INSTANCE_DIR / "models"
    if IS_VERCEL
    else PROJECT_ROOT / "models"
)
UPLOADS_DIR = INSTANCE_DIR / "uploads"
REPORTS_DIR = INSTANCE_DIR / "reports"
PLOTS_DIR = INSTANCE_DIR / "plots"


def ensure_runtime_directories() -> None:
    """Create directories used for generated runtime files."""
    for directory in (MODELS_DIR, UPLOADS_DIR, REPORTS_DIR, PLOTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
