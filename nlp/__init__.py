# nlp/__init__.py
# Makes nlp/ a Python package.
# Exposes the main preprocessing pipeline for easy import.

from nlp.preprocessing_pipeline import run as preprocess

__all__ = ["preprocess"]