# backend/models/__init__.py
# Makes backend/models/ a Python package.
# Exposes request and response models for easy import.

from backend.models.request_models  import QueryRequest
from backend.models.response_models import QueryResponse, HealthResponse

__all__ = [
    "QueryRequest",
    "QueryResponse",
    "HealthResponse",
]