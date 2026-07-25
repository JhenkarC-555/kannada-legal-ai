# backend/routes/__init__.py
# Makes backend/routes/ a Python package.
# Exposes both routers for easy import in app.py.

from backend.routes.query  import router as query_router
from backend.routes.health import router as health_router

__all__ = [
    "query_router",
    "health_router",
]