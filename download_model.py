# Interactive downloader — detects what's already cached and lets you
# choose which models to download.

from semantic_keywords.extractor import MODEL_REGISTRY, detect_available_models

def main() -> None:
    available = detect_available_models()

    print("\n" + "=" * 60)
    print("  semantic-keywords  —  model downloader")
    print("=" * 60)
    print(f"\n  Cache location: ~/.cache/huggingface/hub\n")

    # ── Show status table ─────────────────────────────────────────────────────
    print(f"  {'#':<4} {'Alias':<12} {'HuggingFace name':<35} {'Size':<8} Status")
    print(f"  {'─'*2}   {'─'*10}   {'─'*33}   {'─'*6}   {'─'*14}")

    aliases = list(MODEL_REGISTRY.keys())
    for i, alias in enumerate(aliases, start=1):
        info   = MODEL_REGISTRY[alias]
        status = "downloaded" if alias in available else "not downloaded"
        marker = "  v" if alias in available else "   "
        print(
            f"{marker} [{i}]  {alias:<12}"
            f"  {info['hf_name']:<35}"
            f"  {info['size']:<8}"
            f"  {status}"
        )

    not_downloaded = [a for a in aliases if a not in available]

    if not not_downloaded:
        print("\n  All models are already downloaded. Nothing to do.\n")
        return

    # ── Ask what to download ──────────────────────────────────────────────────
    print(f"\n  Models not yet downloaded: {', '.join(not_downloaded)}\n")
    print("  Options:")
    print("    Enter one or more numbers separated by spaces  e.g.  1 3")
    print("    Enter 'all'  to download everything not yet cached")
    print("    Press Enter  to cancel\n")

    raw = input("  Your choice: ").strip().lower()

    if not raw:
        print("\n  Cancelled. No models downloaded.\n")
        return

    # Resolve selection to a list of aliases
    to_download: list[str] = []

    if raw == "all":
        to_download = not_downloaded
    else:
        for token in raw.split():
            if token.isdigit() and 1 <= int(token) <= len(aliases):
                alias = aliases[int(token) - 1]
                if alias in available:
                    print(f"  Skipping [{alias}] — already downloaded.")
                elif alias not in to_download:
                    to_download.append(alias)
            else:
                print(f"  Ignoring unrecognised input: '{token}'")

    if not to_download:
        print("\n  Nothing new to download.\n")
        return

    # ── Download selected models ──────────────────────────────────────────────
    from sentence_transformers import SentenceTransformer

    print()
    for alias in to_download:
        hf_name = MODEL_REGISTRY[alias]["hf_name"]
        size    = MODEL_REGISTRY[alias]["size"]
        print(f"  Downloading [{alias}]  {hf_name}  ({size}) ...")
        try:
            SentenceTransformer(hf_name)
            print(f"  Done — [{alias}] is ready.\n")
        except Exception as e:
            print(f"  Failed to download [{alias}]: {e}\n")

    # ── Final status ──────────────────────────────────────────────────────────
    available_after = detect_available_models()
    print("=" * 60)
    print("  Download complete. Current status:\n")
    for alias in aliases:
        status = "ready" if alias in available_after else "not downloaded"
        print(f"    [{alias:<10}]  {status}")
    print()


if __name__ == "__main__":
    main()