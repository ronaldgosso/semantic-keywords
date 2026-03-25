from extractor import extract, list_models

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
        "label": "Short sentence (edge case)",
        "text": "The cat sat on the mat.",
    },
    {
        "label": "Empty string (edge case)",
        "text": "",
    },
    {
        "label": "Explicit model='fast' + top_n=3",
        "text": """
            Tanzania is rapidly developing its technology sector, with Dar es Salaam
            emerging as a fintech hub. Mobile money platforms have transformed
            financial access across East Africa.
        """,
        "kwargs": {"model": "fast", "top_n": 3},
    },
]

for test in TESTS:
    print(f"\n── {test['label']} {'─' * max(0, 48 - len(test['label']))}")
    kwargs = test.get("kwargs", {})
    results = extract(test["text"], **kwargs) if test["text"] else []
    if not results:
        print("  (no keywords returned)")
    for r in results:
        bar = "█" * int(r["score"] * 30)
        print(f"  {r['score']:.4f}  {r['keyword']:<30}  {bar}")

print("\n── list_models() ────────────────────────────────")
for alias, hf_name in list_models().items():
    print(f"  {alias:<10}  →  {hf_name}")