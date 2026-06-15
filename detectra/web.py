"""Flask application assembly for Detectra."""

from datetime import datetime

from flask import Flask

from detectra.config import Config
from detectra.paths import ensure_runtime_directories
from detectra.routes import register_routes
from detectra.services.runtime_files import cleanup_old_files


def create_web_app() -> Flask:
    """Create and configure the Detectra Flask application."""
    ensure_runtime_directories()
    application = Flask(__name__)
    application.config.from_object(Config)
    cleanup_old_files(
        (
            application.config["UPLOAD_FOLDER"],
            application.config["PLOTS_FOLDER"],
            application.config["REPORTS_FOLDER"],
        )
    )
    register_routes(application)

    @application.context_processor
    def inject_template_globals():
        return {"current_year": datetime.now().year}

    return application


app = create_web_app()
