"""Detectra application package."""

def create_app():
    """Return the configured Flask application."""
    from detectra.web import app

    return app


__all__ = ["create_app"]
