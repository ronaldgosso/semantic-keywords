# test_extractor.py
# Run: python test_extractor.py
# Detects downloaded models, prompts you to pick one, runs all tests
# including file-based extraction, then drops into a live demo.

from __future__ import annotations
import os
import tempfile
from pathlib import Path

from semantic_keywords import (
    extract,
    extract_file,
    read_file,
    list_models,
    prompt_model_selection,
)

# ── Header ────────────────────────────────────────────────────────────────────
print("=" * 62)
print("  semantic-keywords  —  test suite + live demo")
print("=" * 62)

chosen_model = prompt_model_selection()


def show_results(results: list[dict], top_n: int = 5) -> None:
    actual = results[:top_n]
    if not actual:
        print("  (no keywords returned)\n")
        return
    width = max(len(r["keyword"]) for r in actual) + 2
    print(f"  {'#':<4} {'Keyword':<{width}} {'Score':<8} Relevance")
    print(f"  {'─'*2}   {'─'*(width-2)}   {'─'*6}   {'─'*22}")
    for rank, r in enumerate(actual, start=1):
        bar   = "█" * int(r["score"] * 28)
        empty = "░" * (28 - len(bar))
        print(f"  {rank:<4} {r['keyword']:<{width}} {r['score']:.4f}   {bar}{empty}")
    print()


# ── Text-based tests ──────────────────────────────────────────────────────────

TEXT_TESTS = [
    {
        "label": "Tech / Africa",
        "text": """
            Tanzania is rapidly developing its technology sector, with Dar es Salaam
            emerging as a fintech hub. Mobile money platforms like M-Pesa have
            transformed financial access across East Africa. Local startups are building
            AI-powered agricultural tools to help smallholder farmers with crop prediction.
        """,
        "top_n": 5,
    },
    {
        "label": "Climate science",
        "text": """
            Rising global temperatures are accelerating the melting of Arctic ice sheets,
            leading to higher sea levels and more extreme weather events. Greenhouse gas
            emissions, particularly carbon dioxide from fossil fuels, are the primary
            driver of climate change according to the latest IPCC report.
        """,
        "top_n": 5,
    },
    {
        "label": "Healthcare / AI",
        "text": """
            Machine learning models are being deployed in hospitals to assist radiologists
            with early detection of tumours in medical imaging. Deep learning algorithms
            trained on thousands of CT scans can identify anomalies with high accuracy,
            reducing diagnostic errors and improving patient outcomes.
        """,
        "top_n": 5,
    },
    {
        "label": "Top 3 only",
        "text": """
            Python is a high-level programming language known for its simplicity.
            It is widely used in data science, web development, automation,
            and artificial intelligence research.
        """,
        "top_n": 3,
    },
    {
        "label": "Short phrase (edge case)",
        "text": "Mobile money East Africa",
        "top_n": 5,
    },
    {
        "label": "Empty string (edge case)",
        "text": "",
        "top_n": 5,
    },
    {
        "label": "diversity=0.3 vs diversity=0.9",
        "text": """
            Tanzania is rapidly developing its technology sector, with Dar es Salaam
            emerging as a fintech hub. Mobile money platforms like M-Pesa have
            transformed financial access across East Africa.
        """,
        "top_n": 5,
        "compare_diversity": True,
    },
]

print(f"  Running text tests with model: [{chosen_model}]\n")
print("=" * 62)

for test in TEXT_TESTS:
    label = test["label"]
    text  = test["text"]
    top_n = test["top_n"]
    print(f"\n── {label} {'─' * max(0, 56 - len(label))}")

    if test.get("compare_diversity"):
        for div, tag in [
            (0.3, "diversity=0.3  (more relevant)"),
            (0.9, "diversity=0.9  (more varied)"),
        ]:
            print(f"\n  [{tag}]")
            show_results(extract(text, model=chosen_model, top_n=top_n, diversity=div), top_n)
    else:
        results = extract(text, model=chosen_model, top_n=top_n) if text else []
        show_results(results, top_n)

# ── File-based tests ──────────────────────────────────────────────────────────

print("\n" + "=" * 62)
print("  File extraction tests")
print("=" * 62)

# ── Test 1: .txt file (created on the fly) ────────────────────────────────────
print("\n── extract_file()  →  .txt  ──────────────────────────────────")

TXT_CONTENT = """
Tanzania is rapidly developing its technology sector, with Dar es Salaam
emerging as a fintech hub. Mobile money platforms like M-Pesa have
transformed financial access across East Africa. Local startups are building
AI-powered agricultural tools to help smallholder farmers with crop prediction.
"""

with tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", delete=False, encoding="utf-8"
) as tmp:
    tmp.write(TXT_CONTENT)
    tmp_txt = tmp.name

try:
    result = extract_file(tmp_txt, top_n=5, model=chosen_model)
    print(f"  File   : {result['file']}")
    print(f"  Size   : {result['size_kb']} KB")
    print(f"  Words  : {result['words']}")
    print(f"  Model  : {result['model']}")
    show_results(result["keywords"], 5)
finally:
    os.unlink(tmp_txt)

# ── Test 2: .md file ──────────────────────────────────────────────────────────
print("\n── extract_file()  →  .md  ───────────────────────────────────")

MD_CONTENT = """
# Blockchain and Decentralised Finance

Blockchain technology underpins cryptocurrencies like Bitcoin and Ethereum,
providing a decentralised ledger for secure peer-to-peer transactions.
Smart contracts automate agreements without intermediaries. DeFi platforms
allow lending, borrowing, and trading of digital assets without traditional banks.
Non-fungible tokens (NFTs) use blockchain to verify ownership of digital art.
"""

with tempfile.NamedTemporaryFile(
    mode="w", suffix=".md", delete=False, encoding="utf-8"
) as tmp:
    tmp.write(MD_CONTENT)
    tmp_md = tmp.name

try:
    result = extract_file(tmp_md, top_n=5, model=chosen_model)
    print(f"  File   : {result['file']}")
    print(f"  Words  : {result['words']}")
    show_results(result["keywords"], 5)
finally:
    os.unlink(tmp_md)

# ── Test 3: PDF (if pypdf installed) ─────────────────────────────────────────
print("\n── extract_file()  →  .pdf  (skipped if pypdf not installed) ─")
try:
    import pypdf  # noqa: F401
    print("  pypdf detected — to test PDF extraction pass a real PDF path:")
    print("  result = extract_file('your_file.pdf', top_n=10)")
    print("  (automated PDF creation requires reportlab; run manually instead)\n")
except ImportError:
    print("  pypdf not installed — PDF support inactive.")
    print("  To enable:  pip install pypdf\n")

# ── Test 4: read_file() directly ─────────────────────────────────────────────
print("\n── read_file()  →  returns raw text  ────────────────────────")
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".txt", delete=False, encoding="utf-8"
) as tmp:
    tmp.write("Nairobi is a growing hub for fintech and mobile payments in Africa.")
    tmp_read = tmp.name

try:
    text = read_file(tmp_read)
    preview = text.strip()[:80]
    print(f"  Extracted text: \"{preview}\"")
    print(f"  Word count    : {len(text.split())}\n")
finally:
    os.unlink(tmp_read)

# ── Test 5: error handling ────────────────────────────────────────────────────
print("\n── Error handling  ───────────────────────────────────────────")

tests_errors = [
    ("nonexistent.pdf",  FileNotFoundError, "missing file"),
    ("report.xyz",       ValueError,        "unsupported extension"),
]

for bad_path, expected_exc, label in tests_errors:
    try:
        read_file(bad_path)
        print(f"  FAIL  [{label}] — no exception raised")
    except expected_exc as e:
        print(f"  PASS  [{label}] — {type(e).__name__}: {str(e)[:60]}")
    except Exception as e:
        print(f"  FAIL  [{label}] — unexpected {type(e).__name__}: {e}")
print()

# ── Model registry ────────────────────────────────────────────────────────────
print("── Model registry " + "─" * 44)
print(f"\n  {'Alias':<12} {'HuggingFace name':<35} {'Size':<8} Note")
print(f"  {'─'*10}   {'─'*33}   {'─'*6}   {'─'*30}")
for alias, info in list_models().items():
    marker = " *" if alias == chosen_model else "  "
    print(
        f"{marker} {alias:<12}"
        f"  {info['hf_name']:<35}"
        f"  {info['size']:<8}"
        f"  {info['note']}"
    )
print(f"\n  * = model used in this run\n")
print("=" * 62)

# ── Live demo ─────────────────────────────────────────────────────────────────
print("\n  All tests done. Try it yourself:\n")
print("  Options:")
print("    [1]  Type or paste text")
print("    [2]  Enter a file path  (.pdf / .txt / .md)")
print("    [q]  Quit\n")

while True:
    choice = input("  Choose [1/2/q]: ").strip().lower()

    if choice == "q" or choice == "":
        print("\n  Goodbye!\n")
        break

    if choice not in ("1", "2"):
        print("  Enter 1, 2, or q.")
        continue

    text = ""

    if choice == "1":
        print("\n  Type/paste your text. Press Enter twice when done.\n")
        lines: list[str] = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        text = "\n".join(lines).strip()
        if not text:
            print("  No text entered.\n")
            continue

    elif choice == "2":
        raw = input("\n  File path: ").strip().strip('"')
        if not raw:
            print("  No path entered.\n")
            continue
        p = Path(raw)
        if not p.exists():
            print(f"  Not found: '{raw}'\n")
            continue
        print(f"  Reading '{p.name}' ...")
        try:
            text = read_file(p)
            print(f"  {len(text.split())} words extracted.\n")
        except (ImportError, ValueError) as e:
            print(f"  Error: {e}\n")
            continue

    while True:
        raw_n = input("  Top N keywords? [default 5]: ").strip()
        if raw_n == "":
            top_n = 5
            break
        if raw_n.isdigit() and int(raw_n) >= 1:
            top_n = int(raw_n)
            break
        print("  Enter a positive number.")

    print(f"\n  Extracting top {top_n} keywords  [model: {chosen_model}] ...\n")
    results = extract(text, model=chosen_model, top_n=top_n)
    show_results(results, top_n)

    again = input("  Try another? [y/N]: ").strip().lower()
    print()
    if again != "y":
        print("  Done. Goodbye!\n")
        break