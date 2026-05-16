# rag/__init__.py
# Makes rag/ a Python package.
# Exposes the main RAG pipeline answer function for easy import.

from rag.rag_pipeline import answer

__all__ = ["answer"]