# semantic_keywords/__init__.py
"""
semantic-keywords
~~~~~~~~~~~~~~~~~
AI-powered semantic keyword extraction using sentence embeddings and MMR.
"""

from .extractor import (
    DEFAULT_MODEL,
    MODEL_REGISTRY,
    detect_available_models,
    extract,
    list_models,
    prompt_model_selection,
)

__version__ = "0.1.0"
__all__ = [
    "extract",
    "detect_available_models",
    "prompt_model_selection",
    "list_models",
    "MODEL_REGISTRY",
    "DEFAULT_MODEL",
]
