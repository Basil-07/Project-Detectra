"""Vercel serverless entry point."""

from detectra import create_app


app = create_app()
