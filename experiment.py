import numpy as np
from sentence_transformers import SentenceTransformer

# ── Load model from local cache (no internet needed after download) ──────────
model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)


def embed(text: str) -> np.ndarray:
    """Convert a string into a 384-dimensional vector."""
    return model.encode(text, normalize_embeddings=True)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Measure how similar two vectors are.
    1.0  = identical meaning
    0.0  = completely unrelated
    -1.0 = opposite meaning
    Because we normalize embeddings above, this is just a dot product.
    """
    return float(np.dot(a, b))


def compare(label_a: str, label_b: str, text_a: str, text_b: str) -> None:
    score = cosine_similarity(embed(text_a), embed(text_b))
    bar = "█" * int(score * 30)
    print(f"  {label_a!r:30s} ↔  {label_b!r:30s}  {score:.3f}  {bar}")


# ── Experiment 1: Semantic similarity ────────────────────────────────────────
print("\n── Experiment 1: Does meaning matter? ──────────────────────────────────")
print("  Phrase A                           ↔  Phrase B                           Score")
compare("bank robbery",      "financial crime",   "bank robbery",      "financial crime")
compare("bank robbery",      "river bank",        "bank robbery",      "river bank fishing")
compare("machine learning",  "artificial intel.", "machine learning",  "artificial intelligence")
compare("machine learning",  "banana smoothie",   "machine learning",  "banana smoothie")
compare("Nairobi startup",   "Kenyan tech scene", "Nairobi startup",   "Kenyan tech scene")

# ── Experiment 2: Document → keyword matching (proto-semantic-keywords) ───────
print("\n── Experiment 2: Keyword ranking from a document ────────────────────────")

document = """
Tanzania is rapidly developing its technology sector, with Dar es Salaam
emerging as a fintech hub. Mobile money platforms like M-Pesa have
transformed financial access across East Africa. Local startups are building
AI-powered agricultural tools to help smallholder farmers with crop prediction.
"""

candidates = [
    "fintech hub",
    "mobile money",
    "agricultural AI",
    "smallholder farmers",
    "East Africa technology",
    "banana republic",          # irrelevant — should score low
    "financial access",
    "crop prediction",
    "European football",        # irrelevant — should score low
    "Dar es Salaam startups",
]

doc_vector = embed(document)
scored = []
for phrase in candidates:
    score = cosine_similarity(embed(phrase), doc_vector)
    scored.append((phrase, score))

scored.sort(key=lambda x: x[1], reverse=True)

print("\n  Document snippet: Tanzania fintech, mobile money, agricultural AI...\n")
print(f"  {'Candidate phrase':<30}  Score   Relevance")
print(f"  {'─'*30}  ──────  ─────────")
for phrase, score in scored:
    bar = "█" * int(score * 25)
    tag = "✓ relevant" if score > 0.35 else "✗ filtered"
    print(f"  {phrase:<30}  {score:.3f}   {bar}  {tag}")

print("\n── Top 5 keywords the model would extract ───────────────────────────────")
for phrase, score in scored[:5]:
    print(f"  {score:.3f}  →  {phrase}")
