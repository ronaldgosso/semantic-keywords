# semantic_keywords/cli.py
"""Command-line interface for semantic-keywords."""

from __future__ import annotations

import argparse
import sys
import textwrap

from .extractor import (
    DEFAULT_MODEL,
    MODEL_REGISTRY,
    detect_available_models,
    extract,
    prompt_model_selection,
)

BANNER = """
  ╔══════════════════════════════════════════════╗
  ║         semantic-keywords  v1.0.0            ║
  ║   AI-powered keyword extraction via MMR      ║
  ╚══════════════════════════════════════════════╝
"""


def _print_results(results: list[dict], top_n: int) -> None:
    """Render keyword results as a clean ranked table."""
    if not results:
        print("\n  No keywords found. Try lowering --min-score or using a longer text.\n")
        return

    actual = results[:top_n]
    width = max(len(r["keyword"]) for r in actual) + 2

    print(f"\n  Top {len(actual)} keyword{'s' if len(actual) != 1 else ''}:\n")
    print(f"  {'#':<4} {'Keyword':<{width}} {'Score':<8} Relevance")
    print(f"  {'─'*2}   {'─'*(width-2)}   {'─'*6}   {'─'*22}")

    for rank, r in enumerate(actual, start=1):
        bar = "█" * int(r["score"] * 28)
        empty = "░" * (28 - len(bar))
        print(f"  {rank:<4} {r['keyword']:<{width}} {r['score']:.4f}   {bar}{empty}")

    print()


def _interactive_mode(model: str) -> None:
    """
    Fully guided interactive session:
      1. User pastes or types their text
      2. User picks top N
      3. Optional advanced flags
      4. Results printed
      5. Loop — analyse another text or quit
    """
    print(BANNER)

    while True:
        # ── Text input ────────────────────────────────────────────────────────
        print("  Paste or type your text below.")
        print("  When done, press Enter twice (blank line = end of input).\n")

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
            print("\n  No text entered. Please try again.\n")
            continue

        # ── Top N ─────────────────────────────────────────────────────────────
        print()
        while True:
            raw = input("  How many top keywords? [default: 5]: ").strip()
            if raw == "":
                top_n = 5
                break
            if raw.isdigit() and int(raw) >= 1:
                top_n = int(raw)
                break
            print("  Please enter a whole number (e.g. 3, 5, 10).")

        # ── Optional advanced settings ────────────────────────────────────────
        print()
        adv = input("  Adjust advanced settings? (min-score / diversity) [y/N]: ").strip().lower()

        min_score = 0.20
        diversity = 0.7

        if adv == "y":
            print()
            raw = input(f"  Min similarity score [0.0–1.0, default {min_score}]: ").strip()
            try:
                v = float(raw)
                if 0.0 <= v <= 1.0:
                    min_score = v
                else:
                    print("  Out of range — using default 0.20.")
            except ValueError:
                pass

            raw = input(f"  Diversity factor   [0.0–1.0, default {diversity}]: ").strip()
            try:
                v = float(raw)
                if 0.0 <= v <= 1.0:
                    diversity = v
                else:
                    print("  Out of range — using default 0.70.")
            except ValueError:
                pass

        # ── Extract and display ───────────────────────────────────────────────
        print(f"\n  Extracting keywords  [model: {model}] ...\n")

        results = extract(
            text,
            top_n=top_n,
            min_score=min_score,
            diversity=diversity,
            model=model,
        )

        # Show a short preview of the input text
        preview = textwrap.shorten(text, width=72, placeholder="...")
        print(f'  Input : "{preview}"')
        print(f"  Words : {len(text.split())}")

        _print_results(results, top_n)

        # ── Loop or quit ──────────────────────────────────────────────────────
        again = input("  Analyse another text? [y/N]: ").strip().lower()
        print()
        if again != "y":
            print("  Done. Goodbye!\n")
            break


def _build_parser() -> argparse.ArgumentParser:
    model_choices = list(MODEL_REGISTRY.keys())

    parser = argparse.ArgumentParser(
        prog="semkw",
        description="Extract semantic keywords from text using sentence embeddings + MMR.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        examples:
          semkw                                         # interactive mode (guided prompts)
          semkw "Tanzania fintech mobile money"         # inline text, default top 5
          semkw "Tanzania fintech mobile money" -n 3    # top 3 only
          semkw "climate change arctic ice" --model accurate --scores
          semkw --list-models
          echo "neural networks deep learning" | semkw  # pipe from stdin
        """),
    )

    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Text to extract keywords from. Omit to enter interactive mode.",
    )
    parser.add_argument(
        "--top",
        "-n",
        type=int,
        default=5,
        metavar="N",
        help="Maximum number of keywords to return (default: 5).",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        choices=model_choices,
        metavar="MODEL",
        help=f"Model alias: {', '.join(model_choices)}. Default: auto-detect.",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.20,
        metavar="FLOAT",
        help="Minimum cosine similarity score (default: 0.20).",
    )
    parser.add_argument(
        "--diversity",
        type=float,
        default=0.7,
        metavar="FLOAT",
        help="MMR diversity factor 0.0–1.0 (default: 0.7).",
    )
    parser.add_argument(
        "--scores",
        action="store_true",
        help="Show similarity scores in output.",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Show all models and download status, then exit.",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # ── --list-models ─────────────────────────────────────────────────────────
    if args.list_models:
        available = detect_available_models()
        print(f"\n  {'Alias':<12} {'HuggingFace name':<35} {'Size':<8} {'Status':<14} Note")
        print(f"  {'─'*10}   {'─'*33}   {'─'*6}   {'─'*12}   {'─'*30}")
        for alias, info in MODEL_REGISTRY.items():
            status = "ready" if alias in available else "not downloaded"
            marker = " *" if alias == DEFAULT_MODEL else "  "
            print(
                f"{marker} {alias:<12}"
                f"  {info['hf_name']:<35}"
                f"  {info['size']:<8}"
                f"  {status:<14}"
                f"  {info['note']}"
            )
        print("\n  * = default  |  download missing models: python download_model.py\n")
        sys.exit(0)

    # ── Resolve model (shared by all modes) ───────────────────────────────────
    if args.model:
        model = args.model
    else:
        available = detect_available_models()
        if not available:
            print(
                "\n  No models downloaded. Run: python download_model.py\n",
                file=sys.stderr,
            )
            sys.exit(1)
        model = DEFAULT_MODEL if DEFAULT_MODEL in available else next(iter(available))

    # ── Mode: interactive (no text arg, no stdin pipe) ────────────────────────
    if args.text is None and sys.stdin.isatty():
        # Show model selection menu before entering interactive loop
        model = prompt_model_selection()
        _interactive_mode(model)
        return

    # ── Mode: stdin pipe  (echo "text" | semkw) ───────────────────────────────
    if args.text is None:
        text = sys.stdin.read().strip()
        if not text:
            print("  No input received from stdin.", file=sys.stderr)
            sys.exit(1)
    else:
        # ── Mode: inline  (semkw "text here") ────────────────────────────────
        text = args.text

    # ── Extract (inline + pipe) ───────────────────────────────────────────────
    results = extract(
        text,
        top_n=args.top,
        min_score=args.min_score,
        diversity=args.diversity,
        model=model,
    )

    if args.scores:
        _print_results(results, args.top)
    else:
        # Minimal output: one keyword per line (pipe-friendly)
        for r in results[: args.top]:
            print(r["keyword"])


if __name__ == "__main__":
    main()
