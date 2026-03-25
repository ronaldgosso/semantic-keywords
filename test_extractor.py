# Detects downloaded models, prompts you to pick one, then runs all tests.

from extractor import extract, list_models, prompt_model_selection

# ── Step 1: detect and select model ──────────────────────────────────────────
print("=" * 60)
print("  semantic-keywords  —  test suite")
print("=" * 60)

chosen_model = prompt_model_selection()

# ── Step 2: test cases ────────────────────────────────────────────────────────

TESTS = [
    {
        "label": "Tech / Africa",
        "text": """
            Tanzania is rapidly developing its technology sector, with Dar es Salaam
            emerging as a fintech hub. Mobile money platforms like M-Pesa have
            transformed financial access across East Africa. Local startups are building
            AI-powered agricultural tools to help smallholder farmers with crop prediction.
        """,
    },
    {
        "label": "Climate science",
        "text": """
            Rising global temperatures are accelerating the melting of Arctic ice sheets,
            leading to higher sea levels and more extreme weather events. Greenhouse gas
            emissions, particularly carbon dioxide from fossil fuels, are the primary driver
            of climate change according to the latest IPCC report.
        """,
    },
    {
        "label": "Healthcare / AI",
        "text": """
            Machine learning models are being deployed in hospitals to assist radiologists
            with early detection of tumours in medical imaging. Deep learning algorithms
            trained on thousands of CT scans can identify anomalies with high accuracy,
            reducing diagnostic errors and improving patient outcomes.
        """,
    },
    {
        "label": "Short sentence (edge case)",
        "text": "The cat sat on the mat.",
    },
    {
        "label": "Empty string (edge case)",
        "text": "",
    },
    {
        "label": "diversity=0.3  (less diverse, more relevant)",
        "text": """
            Tanzania is rapidly developing its technology sector, with Dar es Salaam
            emerging as a fintech hub. Mobile money platforms like M-Pesa have
            transformed financial access across East Africa.
        """,
        "kwargs": {"diversity": 0.3, "top_n": 5},
    },
    {
        "label": "diversity=1.0  (maximum diversity)",
        "text": """
            Tanzania is rapidly developing its technology sector, with Dar es Salaam
            emerging as a fintech hub. Mobile money platforms like M-Pesa have
            transformed financial access across East Africa.
        """,
        "kwargs": {"diversity": 1.0, "top_n": 5},
    },
]

# ── Step 3: run tests ─────────────────────────────────────────────────────────

print(f"  Running {len(TESTS)} tests with model: [{chosen_model}]\n")
print("=" * 60)

for test in TESTS:
    label  = test["label"]
    text   = test["text"]
    kwargs = test.get("kwargs", {})

    print(f"\n── {label} {'─' * max(0, 54 - len(label))}")

    results = extract(text, model=chosen_model, **kwargs) if text else []

    if not results:
        print("  (no keywords returned)")
    else:
        print(f"  {'Score':<8} {'Keyword':<32} Bar")
        print(f"  {'─'*6}   {'─'*30}   {'─'*20}")
        for r in results:
            bar = "█" * int(r["score"] * 35)
            print(f"  {r['score']:.4f}   {r['keyword']:<32}  {bar}")

# ── Step 4: show model registry ───────────────────────────────────────────────

print("\n\n── Model registry " + "─" * 42)
print(f"  {'Alias':<12} {'HuggingFace name':<35} {'Size':<8} Note")
print(f"  {'─'*10}   {'─'*33}   {'─'*6}   {'─'*30}")
for alias, info in list_models().items():
    marker = " *" if alias == chosen_model else "  "
    print(
        f"{marker} {alias:<12}"
        f"  {info['hf_name']:<35}"
        f"  {info['size']:<8}"
        f"  {info['note']}"
    )
print("\n  * = model used in this run\n")