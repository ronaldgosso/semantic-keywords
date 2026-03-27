# semantic_keywords/file_api.py
"""
High-level file extraction API.
Combines reader.read_file() + extractor.extract() into one clean call.
"""

from __future__ import annotations

import os
from .reader import read_file, file_info
from .extractor import extract, DEFAULT_MODEL


def extract_file(
    file_path: str | os.PathLike,
    top_n: int = 5,
    min_score: float = 0.20,
    max_words: int = 3,
    model: str = DEFAULT_MODEL,
    diversity: float = 0.7,
) -> dict:
    """
    Read a file and extract its top semantic keywords in one call.

    Parameters
    ----------
    file_path : Path to a .pdf, .txt, or .md file.
    top_n     : Maximum number of keywords to return.
    min_score : Minimum cosine similarity threshold (0.0–1.0).
    max_words : Maximum words per candidate phrase (1–3).
    model     : "fast" | "balanced" | "accurate" | any HF model name.
    diversity : MMR balance factor (0.0 = relevant, 1.0 = diverse).

    Returns
    -------
    dict with keys:
        "file"     : str          — file name
        "size_kb"  : float        — file size in KB
        "words"    : int          — word count of extracted text
        "model"    : str          — model alias used
        "keywords" : list[dict]   — [{"keyword": str, "score": float}, ...]

    Raises
    ------
    FileNotFoundError — file does not exist.
    ValueError        — unsupported format or unreadable PDF.
    ImportError       — pypdf not installed (PDF only).

    Examples
    --------
    >>> from semantic_keywords import extract_file
    >>> result = extract_file("annual_report.pdf", top_n=10, model="balanced")
    >>> for kw in result["keywords"]:
    ...     print(kw["score"], kw["keyword"])

    >>> result = extract_file("notes.txt", top_n=3)
    >>> print(result["keywords"])
    [{"keyword": "mobile money", "score": 0.513}, ...]
    """
    info = file_info(file_path)
    text = read_file(file_path)

    keywords = extract(
        text,
        top_n=top_n,
        min_score=min_score,
        max_words=max_words,
        model=model,
        diversity=diversity,
    )

    return {
        "file":     info["name"],
        "size_kb":  info["size_kb"],
        "words":    len(text.split()),
        "model":    model,
        "keywords": keywords,
    }