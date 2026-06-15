"""Application configuration."""

import os

from dotenv import load_dotenv

from detectra.paths import (
    IS_VERCEL,
    PLOTS_DIR,
    PROJECT_ROOT,
    REPORTS_DIR,
    UPLOADS_DIR,
)


load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """Default configuration shared by local and deployed environments."""

    SECRET_KEY = os.getenv("DETECTRA_SECRET_KEY", "dev-only-change-me")
    MAX_CONTENT_LENGTH = (4 if IS_VERCEL else 16) * 1024 * 1024
    SERVERLESS = IS_VERCEL
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_VERCEL
    UPLOAD_FOLDER = str(UPLOADS_DIR)
    REPORTS_FOLDER = str(REPORTS_DIR)
    PLOTS_FOLDER = str(PLOTS_DIR)
