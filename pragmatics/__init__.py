# pragmatics/__init__.py
# Makes pragmatics/ a Python package.
# Exposes the most used functions for easy import.

from pragmatics.intent_classifier  import classify
from pragmatics.prompt_router      import get_system_prompt, add_disclaimer
from pragmatics.context_tracker    import ContextTracker
from pragmatics.implicature_handler import resolve
from pragmatics.dialect_adapter    import normalize_dialect

__all__ = [
    "classify",
    "get_system_prompt",
    "add_disclaimer",
    "ContextTracker",
    "resolve",
    "normalize_dialect",
]