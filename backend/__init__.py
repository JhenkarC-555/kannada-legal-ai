# backend/__init__.py
# Makes backend/ a Python package.
# Exposes the FastAPI app instance for easy import.

from backend.app import app

__all__ = ["app"]