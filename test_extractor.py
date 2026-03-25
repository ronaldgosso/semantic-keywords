# test_extractor.py
# Detects downloaded models, prompts you to pick one, runs all tests,
# then drops into a live interactive session so you can try your own text.

from semantic_keywords import extract, list_models, prompt_model_selection

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


# ── Test cases ────────────────────────────────────────────────────────────────

TESTS = [
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
            Python is a high-level programming language known for its simplicity and
            readability. It is widely used in data science, web development, automation,
            and artificial intelligence research.
        """,
        "top_n": 3,
    },
    {
        "label": "Top 8 — long text",
        "text": """
            Blockchain technology underpins cryptocurrencies like Bitcoin and Ethereum,
            providing a decentralised ledger for secure peer-to-peer transactions.
            Smart contracts automate agreements without intermediaries. Decentralised
            finance (DeFi) platforms allow lending, borrowing, and trading of digital
            assets without traditional banks. Non-fungible tokens (NFTs) use blockchain
            to verify ownership of digital art and collectibles.
        """,
        "top_n": 8,
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
        "label": "diversity=0.3 vs diversity=0.9  (same text)",
        "text": """
            Tanzania is rapidly developing its technology sector, with Dar es Salaam
            emerging as a fintech hub. Mobile money platforms like M-Pesa have
            transformed financial access across East Africa.
        """,
        "top_n": 5,
        "compare_diversity": True,
    },
]

print(f"  Running {len(TESTS)} tests with model: [{chosen_model}]\n")
print("=" * 62)

for test in TESTS:
    label = test["label"]
    text  = test["text"]
    top_n = test["top_n"]

    print(f"\n── {label} {'─' * max(0, 56 - len(label))}")

    if test.get("compare_diversity"):
        for div, tag in [(0.3, "diversity=0.3  (more relevant, less varied)"),
                         (0.9, "diversity=0.9  (more varied, less repetitive)")]:
            print(f"\n  [{tag}]")
            r = extract(text, model=chosen_model, top_n=top_n, diversity=div)
            show_results(r, top_n)
    else:
        results = extract(text, model=chosen_model, top_n=top_n) if text else []
        show_results(results, top_n)

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
print("\n  All tests passed. Try the package yourself:\n")

while True:
    print("  Enter text to extract keywords from.")
    print("  Press Enter twice when done. Type 'quit' to exit.\n")

    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().lower() == "quit":
            lines = []
            break
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)

    text = "\n".join(lines).strip()

    if not text:
        print("\n  Exiting. Goodbye!\n")
        break

    while True:
        raw = input("\n  Top N keywords? [default 5]: ").strip()
        if raw == "":
            top_n = 5
            break
        if raw.isdigit() and int(raw) >= 1:
            top_n = int(raw)
            break
        print("  Please enter a positive whole number.")

    print(f"\n  Extracting top {top_n} keywords  [model: {chosen_model}] ...\n")
    results = extract(text, model=chosen_model, top_n=top_n)
    show_results(results, top_n)

    again = input("  Try another? [y/N]: ").strip().lower()
    print()
    if again != "y":
        print("  Done. Goodbye!\n")
        break