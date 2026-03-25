# extractor.py  —  Phase 2 (revised with MMR)
from __future__ import annotations

import re
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "this", "that", "these", "those",
    "it", "its", "as", "up", "out", "not", "no", "so", "if", "than",
    "then", "also", "into", "about", "over", "after", "before", "between",
}

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    return _model


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


def _embed(texts: list[str]) -> np.ndarray:
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return b @ a


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


def extract(
    text: str,
    top_n: int = 5,
    min_score: float = 0.20,
    max_words: int = 3,
) -> list[dict]:
    """
    Extract semantically relevant keywords from text using MMR ranking.

    Parameters
    ----------
    text      : Input document.
    top_n     : Max keywords to return.
    min_score : Minimum cosine similarity threshold (0.0–1.0).
    max_words : Max words per candidate phrase.

    Returns
    -------
    List of {"keyword": str, "score": float} dicts, best first.
    """
    if not text or not text.strip():
        return []

    candidates = _extract_candidates(text, max_words=max_words)
    if not candidates:
        return []

    all_texts = [text] + candidates
    embeddings = _embed(all_texts)

    doc_vector = embeddings[0]
    candidate_vectors = embeddings[1:]

    return _mmr(doc_vector, candidate_vectors, candidates, top_n=top_n, min_score=min_score)