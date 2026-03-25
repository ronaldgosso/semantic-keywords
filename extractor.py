# extractor.py
# Phase 2: Core semantic keyword extraction algorithm.
# One file, no package structure yet. Just the brain.

from __future__ import annotations

import re
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Constants ────────────────────────────────────────────────────────────────

MODEL_NAME = "all-MiniLM-L6-v2"

# Words that carry no meaning on their own — we strip these from candidates.
# A phrase made entirely of stopwords (e.g. "the of") gets filtered out.
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "this", "that", "these", "those",
    "it", "its", "as", "up", "out", "not", "no", "so", "if", "than",
    "then", "also", "into", "about", "over", "after", "before", "between",
}

# ── Model loader ─────────────────────────────────────────────────────────────

# We store the model in a module-level variable so it loads only once per
# Python session — not once per function call. This matters: loading takes
# ~1 second. Calling extract() 10 times should pay that cost only once.
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Return the cached model, loading it on first call."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    return _model


# ── Candidate extraction ─────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Lowercase and strip punctuation, keeping spaces and hyphens."""
    text = text.lower()
    text = re.sub(r"[^\w\s\-]", " ", text)   # remove punctuation
    text = re.sub(r"\s+", " ", text)          # collapse whitespace
    return text.strip()


def _extract_candidates(text: str, max_words: int = 3) -> list[str]:
    """
    Pull noun-phrase-like candidates from text.

    Strategy: slide a window of 1, 2, and 3 words across the cleaned text,
    keep only windows where:
      - at least one word is NOT a stopword (has real meaning)
      - no token is a single character (strips stray letters)
      - the phrase has not been seen before (deduplication)

    This is intentionally simple — no POS tagger, no spaCy dependency.
    It catches "mobile money", "fintech hub", "crop prediction" reliably.
    """
    words = _clean(text).split()
    seen: set[str] = set()
    candidates: list[str] = []

    for n in range(1, max_words + 1):           # window sizes: 1, 2, 3
        for i in range(len(words) - n + 1):
            window = words[i : i + n]

            # Skip if every word is a stopword
            if all(w in STOPWORDS for w in window):
                continue

            # Skip single-character tokens
            if any(len(w) <= 1 for w in window):
                continue

            phrase = " ".join(window)
            if phrase not in seen:
                seen.add(phrase)
                candidates.append(phrase)

    return candidates


# ── Embedding + ranking ──────────────────────────────────────────────────────

def _embed(texts: list[str]) -> np.ndarray:
    """
    Embed a list of strings in one batch call.
    Batching is faster than calling model.encode() once per string.
    normalize_embeddings=True means cosine similarity = dot product.
    """
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Dot product between one vector (a) and a matrix of vectors (b).
    Returns a 1-D array of similarity scores, one per row in b.
    This works because both a and b are already L2-normalised.
    """
    return b @ a   # shape: (n_candidates,)


# ── Public API ───────────────────────────────────────────────────────────────

def extract(
    text: str,
    top_n: int = 5,
    min_score: float = 0.20,
    max_words: int = 3,
) -> list[dict]:
    """
    Extract the most semantically relevant keywords from a text.

    Parameters
    ----------
    text      : The input document (any length).
    top_n     : Maximum number of keywords to return.
    min_score : Minimum cosine similarity to include a keyword (0.0–1.0).
                Lower = more keywords, less precise.
                Higher = fewer keywords, more precise.
    max_words : Maximum words per candidate phrase (1–3 recommended).

    Returns
    -------
    List of dicts, each with keys:
        "keyword" : str   — the keyword phrase
        "score"   : float — cosine similarity to the document (0.0–1.0)

    Example
    -------
    >>> results = extract("Tanzania is a hub for mobile money fintech.")
    >>> results[0]
    {'keyword': 'mobile money', 'score': 0.512}
    """
    if not text or not text.strip():
        return []

    # Step 1: get candidates
    candidates = _extract_candidates(text, max_words=max_words)
    if not candidates:
        return []

    # Step 2: embed document + all candidates in one batch
    all_texts = [text] + candidates
    embeddings = _embed(all_texts)

    doc_vector = embeddings[0]            # shape: (384,)
    candidate_vectors = embeddings[1:]    # shape: (n_candidates, 384)

    # Step 3: score every candidate against the document
    scores = _cosine_similarity(doc_vector, candidate_vectors)

    # Step 4: sort by score descending, apply threshold, take top_n
    ranked_indices = np.argsort(scores)[::-1]

    results = []
    for idx in ranked_indices:
        if len(results) >= top_n:
            break
        score = float(scores[idx])
        if score < min_score:
            break
        results.append({
            "keyword": candidates[idx],
            "score": round(score, 4),
        })

    return results