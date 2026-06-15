"""Application configuration."""

import os

from dotenv import load_dotenv

from detectra.paths import PROJECT_ROOT, PLOTS_DIR, REPORTS_DIR, UPLOADS_DIR


load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """Default configuration shared by local and deployed environments."""

    SECRET_KEY = os.getenv("DETECTRA_SECRET_KEY", "dev-only-change-me")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = str(UPLOADS_DIR)
    REPORTS_FOLDER = str(REPORTS_DIR)
    PLOTS_FOLDER = str(PLOTS_DIR)
