# semantic_keywords/__init__.py
"""
semantic-keywords
~~~~~~~~~~~~~~~~~
AI-powered semantic keyword extraction using sentence embeddings and MMR.

Quick start
-----------
    from semantic_keywords import extract
    results = extract("Tanzania fintech mobile money startups", top_n=5)

File extraction
---------------
    from semantic_keywords import extract_file
    results = extract_file("report.pdf", top_n=10)
"""

from .extractor import (
    DEFAULT_MODEL,
    MODEL_REGISTRY,
    detect_available_models,
    extract,
    list_models,
    prompt_model_selection,
)
from .file_api import extract_file
from .reader import file_info, read_file

__version__ = "0.2.6"

__all__ = [
    # Core extraction
    "extract",
    "extract_file",
    # File reading
    "read_file",
    "file_info",
    # Model utilities
    "detect_available_models",
    "prompt_model_selection",
    "list_models",
    "MODEL_REGISTRY",
    "DEFAULT_MODEL",
]
