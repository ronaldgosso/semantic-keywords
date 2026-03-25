from __future__ import annotations

import re
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Model registry ───────────────────────────────────────────────────────────
# Keys are the user-facing aliases. Values are HuggingFace model identifiers.

MODEL_REGISTRY: dict[str, str] = {
    "fast":     "all-MiniLM-L6-v2",    # 90MB  — default
    "balanced": "all-MiniLM-L12-v2",   # 120MB — more layers, slightly better
    "accurate": "all-mpnet-base-v2",   # 420MB — best quality, slower on CPU
}

DEFAULT_MODEL = "fast"

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "this", "that", "these", "those",
    "it", "its", "as", "up", "out", "not", "no", "so", "if", "than",
    "then", "also", "into", "about", "over", "after", "before", "between",
}

# ── Model cache ──────────────────────────────────────────────────────────────
# One cached instance per model name — so switching models in the same session
# doesn't re-load a model that was already used earlier.

_model_cache: dict[str, SentenceTransformer] = {}


def _resolve_model_name(model: str) -> str:
    """
    Translate a user-facing alias to a HuggingFace model identifier.

    Aliases like "fast" → "all-MiniLM-L6-v2"
    Unknown strings are treated as custom HuggingFace model names directly.

    Examples
    --------
    _resolve_model_name("fast")                    → "all-MiniLM-L6-v2"
    _resolve_model_name("accurate")                → "all-mpnet-base-v2"
    _resolve_model_name("BAAI/bge-small-en-v1.5") → "BAAI/bge-small-en-v1.5"
    """
    return MODEL_REGISTRY.get(model, model)


def _get_model(model: str = DEFAULT_MODEL) -> SentenceTransformer:
    """
    Return a loaded SentenceTransformer, using the cache when possible.

    Parameters
    ----------
    model : alias ("fast", "balanced", "accurate") or any HuggingFace model name.
    """
    hf_name = _resolve_model_name(model)

    if hf_name not in _model_cache:
        # local_files_only=True — never hit the internet after first download.
        # If the model isn't cached locally, this raises a clear error telling
        # the user to run the downloader first.
        try:
            _model_cache[hf_name] = SentenceTransformer(
                hf_name, local_files_only=True
            )
        except Exception:
            raise OSError(
                f"Model '{hf_name}' not found in local cache.\n"
                f"Run this once to download it:\n\n"
                f"    python -c \"from sentence_transformers import SentenceTransformer; "
                f"SentenceTransformer('{hf_name}')\"\n"
            )

    return _model_cache[hf_name]


# ── Text processing ──────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_candidates(text: str, max_words: int = 3) -> list[str]:
    words = _clean(text).split()
    seen: set[str] = set()
    candidates: list[str] = []

    for n in range(1, max_words + 1):
        for i in range(len(words) - n + 1):
            window = words[i : i + n]

            if all(w in STOPWORDS for w in window):
                continue
            if any(len(w) <= 1 for w in window):
                continue
            if n == 1:
                word = window[0]
                if word in STOPWORDS or len(word) < 4:
                    continue

            phrase = " ".join(window)
            if phrase not in seen:
                seen.add(phrase)
                candidates.append(phrase)

    return candidates


# ── Embedding + MMR ──────────────────────────────────────────────────────────

def _embed(texts: list[str], model: str = DEFAULT_MODEL) -> np.ndarray:
    m = _get_model(model)
    return m.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def _mmr(
    doc_vector: np.ndarray,
    candidate_vectors: np.ndarray,
    candidates: list[str],
    top_n: int,
    min_score: float,
    diversity: float = 0.7,
) -> list[dict]:
    relevance = candidate_vectors @ doc_vector

    valid = np.where(relevance >= min_score)[0]
    if len(valid) == 0:
        return []

    selected_indices: list[int] = []
    remaining = list(valid)

    for _ in range(min(top_n, len(valid))):
        if not remaining:
            break

        if not selected_indices:
            best = max(remaining, key=lambda i: relevance[i])
        else:
            selected_vectors = candidate_vectors[selected_indices]
            best_score = -np.inf
            best = remaining[0]

            for i in remaining:
                rel = relevance[i]
                sims_to_selected = candidate_vectors[i] @ selected_vectors.T
                max_redundancy = float(np.max(sims_to_selected))
                mmr_score = diversity * rel - (1 - diversity) * max_redundancy
                if mmr_score > best_score:
                    best_score = mmr_score
                    best = i

        selected_indices.append(best)
        remaining.remove(best)

    return [
        {"keyword": candidates[i], "score": round(float(relevance[i]), 4)}
        for i in selected_indices
    ]


# ── Public API ───────────────────────────────────────────────────────────────

def extract(
    text: str,
    top_n: int = 5,
    min_score: float = 0.20,
    max_words: int = 3,
    model: str = DEFAULT_MODEL,
    diversity: float = 0.7,
) -> list[dict]:
    """
    Extract semantically relevant keywords from text.

    Parameters
    ----------
    text      : Input document (any length).
    top_n     : Maximum number of keywords to return.
    min_score : Minimum cosine similarity to include a result (0.0–1.0).
    max_words : Maximum words per candidate phrase (1–3 recommended).
    model     : Which model to use. Options:
                  "fast"     — all-MiniLM-L6-v2  (90MB,  default)
                  "balanced" — all-MiniLM-L12-v2 (120MB)
                  "accurate" — all-mpnet-base-v2 (420MB)
                  any HuggingFace model name     (custom)
    diversity : MMR diversity factor (0.0–1.0).
                0.0 = pure relevance, may repeat similar phrases.
                1.0 = pure diversity, may miss the most relevant phrase.
                0.7 = recommended default.

    Returns
    -------
    List of {"keyword": str, "score": float} dicts, best first.

    Examples
    --------
    >>> extract("Tanzania fintech mobile money startups")
    [{'keyword': 'mobile money', 'score': 0.513}, ...]

    >>> extract("...", model="accurate", top_n=10)
    [...]

    >>> extract("...", model="BAAI/bge-small-en-v1.5")
    [...]
    """
    if not text or not text.strip():
        return []

    candidates = _extract_candidates(text, max_words=max_words)
    if not candidates:
        return []

    all_texts = [text] + candidates
    embeddings = _embed(all_texts, model=model)

    doc_vector = embeddings[0]
    candidate_vectors = embeddings[1:]

    return _mmr(
        doc_vector, candidate_vectors, candidates,
        top_n=top_n, min_score=min_score, diversity=diversity,
    )


def list_models() -> dict[str, str]:
    """
    Return the built-in model registry.
    Useful for CLI help text and documentation.

    >>> import extractor
    >>> extractor.list_models()
    {'fast': 'all-MiniLM-L6-v2', 'balanced': 'all-MiniLM-L12-v2', ...}
    """
    return dict(MODEL_REGISTRY)