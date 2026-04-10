# semantic_keywords/extractor.py
"""Core extraction logic — candidates, embeddings, MMR ranking."""

from __future__ import annotations

import os
import re

import numpy as np
from sentence_transformers import SentenceTransformer

# ── Model registry ────────────────────────────────────────────────────────────

MODEL_REGISTRY: dict[str, dict[str, str]] = {
    "fast": {
        "hf_name": "all-MiniLM-L6-v2",
        "size": "90MB",
        "note": "fastest, great for most use cases",
    },
    "balanced": {
        "hf_name": "all-MiniLM-L12-v2",
        "size": "120MB",
        "note": "slightly better accuracy, still fast",
    },
    "accurate": {
        "hf_name": "all-mpnet-base-v2",
        "size": "420MB",
        "note": "best quality, slower on CPU",
    },
}

DEFAULT_MODEL = "fast"

STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "as",
    "up",
    "out",
    "not",
    "no",
    "so",
    "if",
    "than",
    "then",
    "also",
    "into",
    "about",
    "over",
    "after",
    "before",
    "between",
}

_model_cache: dict[str, SentenceTransformer] = {}


def _get_hf_cache_dir() -> str:
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        return os.path.join(hf_home, "hub")
    hub_cache = os.environ.get("HUGGINGFACE_HUB_CACHE")
    if hub_cache:
        return hub_cache
    return os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")


def _is_model_cached(hf_name: str) -> bool:
    cache_dir = _get_hf_cache_dir()
    if not os.path.isdir(cache_dir):
        return False
    candidates = [
        f"models--sentence-transformers--{hf_name}",
        f"models--{hf_name.replace('/', '--')}",
    ]
    for folder in candidates:
        full_path = os.path.join(cache_dir, folder)
        if os.path.isdir(full_path):
            snapshots = os.path.join(full_path, "snapshots")
            if os.path.isdir(snapshots) and os.listdir(snapshots):
                return True
    return False


def detect_available_models() -> dict[str, dict[str, str]]:
    """Return only the models that are downloaded and ready to use offline."""
    return {
        alias: info for alias, info in MODEL_REGISTRY.items() if _is_model_cached(info["hf_name"])
    }


def prompt_model_selection() -> str:
    """
    Detect downloaded models and prompt the user to choose one.
    Returns the chosen alias string ("fast", "balanced", or "accurate").
    """
    available = detect_available_models()

    if not available:
        print("\n  No models found in local cache.")
        print("  Run download_model.py to download at least one:\n")
        for alias, info in MODEL_REGISTRY.items():
            print(f"    [{alias:<10}]  {info['hf_name']:<35}  {info['size']}")
        print("\n  Example:\n    python download_model.py\n")
        raise SystemExit(1)

    if len(available) == 1:
        alias = next(iter(available))
        info = available[alias]
        print(f"\n  Auto-selected: [{alias}]  {info['hf_name']}  ({info['size']})")
        print("  Tip: download more models with python download_model.py\n")
        return alias

    aliases = list(available.keys())
    print("\n  Available models (downloaded and ready):\n")
    for i, alias in enumerate(aliases, start=1):
        info = available[alias]
        marker = " *" if alias == DEFAULT_MODEL else "  "
        print(
            f"  {marker} [{i}]  {alias:<10}"
            f"  {info['hf_name']:<35}"
            f"  {info['size']:<7}"
            f"  {info['note']}"
        )
    print("\n       * = default\n")

    while True:
        raw = input(
            f"  Select model [1–{len(aliases)}] (Enter = default '{DEFAULT_MODEL}'): "
        ).strip()

        if raw == "":
            chosen = DEFAULT_MODEL if DEFAULT_MODEL in available else aliases[0]
            print(f"  Using: {chosen}\n")
            return chosen

        if raw.isdigit() and 1 <= int(raw) <= len(aliases):
            chosen = aliases[int(raw) - 1]
            print(f"  Using: {chosen}\n")
            return chosen

        print(f"  Please enter a number between 1 and {len(aliases)}, or press Enter.")


def _resolve_model_name(model: str) -> str:
    return MODEL_REGISTRY[model]["hf_name"] if model in MODEL_REGISTRY else model


def _get_model(model: str = DEFAULT_MODEL) -> SentenceTransformer:
    hf_name = _resolve_model_name(model)
    if hf_name not in _model_cache:
        try:
            _model_cache[hf_name] = SentenceTransformer(hf_name, local_files_only=True)
        except Exception:
            raise OSError(
                f"Model '{hf_name}' not found in local cache.\n"
                f"Run download_model.py to download it first.\n"
            )
    return _model_cache[hf_name]


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


def _embed(texts: list[str], model: str = DEFAULT_MODEL) -> np.ndarray:
    m = _get_model(model)
    output = m.encode(texts, normalize_embeddings=True, show_progress_bar=False)  # type: ignore[assignment]
    if hasattr(output, "cpu"):
        return np.asarray(output.cpu().numpy())
    return np.asarray(output)


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
        {"keyword": candidates[i], "score": round(float(relevance[i]), 4)} for i in selected_indices
    ]


def extract(
    text: str,
    top_n: int = 5,
    min_score: float = 0.20,
    max_words: int = 3,
    model: str = DEFAULT_MODEL,
    diversity: float = 0.7,
) -> list[dict]:
    """
    Extract semantically relevant keywords from text using MMR ranking.

    Parameters
    ----------
    text      : Input document (any length).
    top_n     : Maximum number of keywords to return.
    min_score : Minimum cosine similarity threshold (0.0–1.0).
    max_words : Maximum words per candidate phrase (1–3 recommended).
    model     : "fast" | "balanced" | "accurate" | any HuggingFace model name.
    diversity : MMR balance factor (0.0 = pure relevance, 1.0 = pure diversity).

    Returns
    -------
    List of {"keyword": str, "score": float} dicts, best first.

    Examples
    --------
    >>> from semantic_keywords import extract
    >>> extract("Tanzania fintech mobile money startups")
    [{'keyword': 'mobile money', 'score': 0.513}, ...]
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
        doc_vector,
        candidate_vectors,
        candidates,
        top_n=top_n,
        min_score=min_score,
        diversity=diversity,
    )


def list_models() -> dict[str, dict[str, str]]:
    """Return the full model registry."""
    return dict(MODEL_REGISTRY)
