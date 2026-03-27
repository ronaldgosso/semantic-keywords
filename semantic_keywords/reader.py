# semantic_keywords/reader.py
"""
File reading utilities for semantic-keywords.

Supported formats
-----------------
.pdf   — extracted via pypdf (optional dependency)
.txt   — read as UTF-8, fallback to latin-1
.md    — same as .txt

Usage
-----
    from semantic_keywords.reader import read_file
    text = read_file("report.pdf")
"""

from __future__ import annotations

import os
from pathlib import Path

# Formats we can handle
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def _read_pdf(path: Path) -> str:
    """
    Extract all text from a PDF using pypdf.
    Raises ImportError with install instructions if pypdf is not installed.
    Raises ValueError if the PDF yields no extractable text (e.g. scanned image PDF).
    """
    try:
        import pypdf  # noqa: PLC0415
    except ImportError:
        raise ImportError(
            "pypdf is required to read PDF files.\n"
            "Install it with:\n\n"
            "    pip install pypdf\n\n"
            "Or install the full file-reading extras:\n\n"
            "    pip install semantic-keywords[files]\n"
        )

    pages: list[str] = []
    with open(path, "rb") as fh:
        reader = pypdf.PdfReader(fh)
        if reader.is_encrypted:
            raise ValueError(
                f"'{path.name}' is password-protected. "
                "Decrypt the PDF before extracting keywords."
            )
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)

    if not pages:
        raise ValueError(
            f"No extractable text found in '{path.name}'.\n"
            "This is usually a scanned/image-only PDF. "
            "Run it through an OCR tool first (e.g. Adobe, tesseract)."
        )

    return "\n\n".join(pages)


def _read_text(path: Path) -> str:
    """Read a plain-text or markdown file, trying UTF-8 then latin-1."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def read_file(file_path: str | os.PathLike) -> str:
    """
    Read a file and return its text content as a single string.

    Parameters
    ----------
    file_path : Path to a .pdf, .txt, or .md file.

    Returns
    -------
    str — the full extracted text, ready to pass into extract().

    Raises
    ------
    FileNotFoundError  — file does not exist.
    ValueError         — unsupported extension, encrypted PDF,
                         or image-only PDF with no extractable text.
    ImportError        — pypdf not installed (PDF files only).

    Examples
    --------
    >>> from semantic_keywords import read_file, extract
    >>> text    = read_file("annual_report.pdf")
    >>> results = extract(text, top_n=10)
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: '{path}'")

    if not path.is_file():
        raise ValueError(f"'{path}' is a directory, not a file.")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: '{ext}'.\n"
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if ext == ".pdf":
        return _read_pdf(path)
    else:
        return _read_text(path)


def file_info(file_path: str | os.PathLike) -> dict:
    """
    Return basic metadata about a file without reading all its content.
    Useful for CLI display before extraction runs.

    Returns
    -------
    dict with keys: name, extension, size_kb, exists
    """
    path = Path(file_path)
    return {
        "name":      path.name,
        "extension": path.suffix.lower(),
        "size_kb":   round(path.stat().st_size / 1024, 1) if path.exists() else 0,
        "exists":    path.exists(),
    }