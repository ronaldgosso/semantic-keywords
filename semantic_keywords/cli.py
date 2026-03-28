# semantic_keywords/cli.py
"""Command-line interface for semantic-keywords."""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

from .extractor import (
    DEFAULT_MODEL,
    MODEL_REGISTRY,
    detect_available_models,
    extract,
    prompt_model_selection,
)
from .file_api import extract_file
from .reader import SUPPORTED_EXTENSIONS, file_info, read_file

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


def _print_file_header(info: dict, model: str) -> None:
    """Print a summary line before file extraction results."""
    print(f"\n  File  : {info['name']}")
    print(f"  Size  : {info['size_kb']} KB")
    print(f"  Model : {model}")


def _resolve_model(model_arg: str | None) -> str:
    """Pick model from arg or auto-detect from downloaded models."""
    if model_arg:
        return model_arg
    available = detect_available_models()
    if not available:
        print(
            "\n  No models downloaded. Run: python download_model.py\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return DEFAULT_MODEL if DEFAULT_MODEL in available else next(iter(available))


# ── Interactive mode ──────────────────────────────────────────────────────────


def _interactive_mode(model: str) -> None:
    """
    Fully guided interactive session supporting both text input and file paths.
    """
    print(BANNER)

    while True:
        # ── Input method ──────────────────────────────────────────────────────
        print("  Input source:\n")
        print("    [1]  Type or paste text")
        ext_list = "  /  ".join(sorted(SUPPORTED_EXTENSIONS))
        print(f"    [2]  Load from file  ({ext_list})")
        print()

        while True:
            choice = input("  Choose [1/2]: ").strip()
            if choice in ("1", "2"):
                break
            print("  Enter 1 or 2.")

        text = ""
        input_label = ""

        # ── Option 1: text input ──────────────────────────────────────────────
        if choice == "1":
            print()
            print("  Paste or type your text below.")
            print("  Press Enter twice (blank line) when done.\n")

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

            preview = textwrap.shorten(text, width=64, placeholder="...")
            input_label = f'"{preview}"'

        # ── Option 2: file input ──────────────────────────────────────────────
        else:
            print()
            while True:
                raw_path = input("  File path (drag & drop or type): ").strip().strip('"')
                if not raw_path:
                    print("  No path entered. Try again.")
                    continue

                path = Path(raw_path)

                if not path.exists():
                    print(f"  File not found: '{raw_path}'. Check the path and try again.")
                    continue

                ext = path.suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    print(
                        f"  Unsupported format '{ext}'. "
                        f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                    )
                    continue

                # Try to read the file before continuing
                print(f"\n  Reading '{path.name}' ...")
                try:
                    text = read_file(path)
                except ImportError as e:
                    print(f"\n  {e}")
                    continue
                except ValueError as e:
                    print(f"\n  {e}")
                    continue

                info = file_info(path)
                input_label = f"{info['name']}  ({info['size_kb']} KB,  {len(text.split())} words)"
                break

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

        # ── Optional advanced settings ─────────────────────────────────────
        print()
        adv = input("  Adjust advanced settings? (min-score / diversity) [y/N]: ").strip().lower()

        min_score = 0.20
        diversity = 0.7

        if adv == "y":
            print()
            raw = input(f"  Min similarity score [0.0–1.0, default {min_score}]: ").strip()
            try:
                v = float(raw)
                min_score = v if 0.0 <= v <= 1.0 else min_score
            except ValueError:
                pass

            raw = input(f"  Diversity factor   [0.0–1.0, default {diversity}]: ").strip()
            try:
                v = float(raw)
                diversity = v if 0.0 <= v <= 1.0 else diversity
            except ValueError:
                pass

        # ── Extract & display ──────────────────────────────────────────────
        print(f"\n  Extracting keywords  [model: {model}] ...\n")
        print(f"  Input : {input_label}")
        print(f"  Words : {len(text.split())}")

        results = extract(
            text,
            top_n=top_n,
            min_score=min_score,
            diversity=diversity,
            model=model,
        )
        _print_results(results, top_n)

        # ── Loop or quit ───────────────────────────────────────────────────
        again = input("  Analyse another? [y/N]: ").strip().lower()
        print()
        if again != "y":
            print("  Done. Goodbye!\n")
            break


# ── CLI argument parser ───────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    model_choices = list(MODEL_REGISTRY.keys())
    ext_list = "  ".join(sorted(SUPPORTED_EXTENSIONS))

    parser = argparse.ArgumentParser(
        prog="semkw",
        description="Extract semantic keywords from text or files using embeddings + MMR.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(f"""
        supported file types:
          {ext_list}

        examples:
          semkw                                            # interactive mode
          semkw "Tanzania fintech mobile money"            # inline text
          semkw "climate change arctic" -n 8 --scores     # top 8 with scores
          semkw --file report.pdf                          # extract from PDF
          semkw --file notes.txt -n 3 --model accurate    # txt, top 3, best model
          semkw --file report.pdf --scores                 # PDF with score table
          echo "neural networks deep learning" | semkw    # pipe from stdin
          semkw --list-models                              # show model status
        """),
    )

    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Inline text to extract keywords from. Omit to enter interactive mode.",
    )
    parser.add_argument(
        "--file",
        "-f",
        default=None,
        metavar="PATH",
        help=f"Path to a file to extract keywords from ({ext_list}).",
    )
    parser.add_argument(
        "--top",
        "-n",
        type=int,
        default=5,
        metavar="N",
        help="Maximum keywords to return (default: 5).",
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
        help="Minimum cosine similarity score 0.0–1.0 (default: 0.20).",
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
        help="Show ranked score table instead of plain keyword list.",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Show all models and their download status, then exit.",
    )

    return parser


# ── Entry point ───────────────────────────────────────────────────────────────


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
        print("\n  * = default  |  download missing: python download_model.py\n")
        sys.exit(0)

    model = _resolve_model(args.model)

    # ── --file mode ───────────────────────────────────────────────────────────
    if args.file:
        path = Path(args.file)

        # Validate before reading
        if not path.exists():
            print(f"\n  File not found: '{args.file}'\n", file=sys.stderr)
            sys.exit(1)

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            print(
                f"\n  Unsupported file type '{ext}'.\n"
                f"  Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}\n",
                file=sys.stderr,
            )
            sys.exit(1)

        info = file_info(path)
        print(f"\n  Reading '{info['name']}'  ({info['size_kb']} KB) ...")

        try:
            result = extract_file(
                path,
                top_n=args.top,
                min_score=args.min_score,
                diversity=args.diversity,
                model=model,
            )
        except ImportError as e:
            print(f"\n  {e}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"\n  {e}", file=sys.stderr)
            sys.exit(1)

        print(f"  Words : {result['words']}")
        print(f"  Model : {result['model']}")

        if args.scores:
            _print_results(result["keywords"], args.top)
        else:
            print()
            for kw in result["keywords"]:
                print(kw["keyword"])
            print()

        return

    # ── Interactive mode (no text arg, no file, no stdin pipe) ───────────────
    if args.text is None and sys.stdin.isatty():
        model = prompt_model_selection()
        _interactive_mode(model)
        return

    # ── Stdin pipe mode ───────────────────────────────────────────────────────
    if args.text is None:
        text = sys.stdin.read().strip()
        if not text:
            print("  No input received from stdin.", file=sys.stderr)
            sys.exit(1)
    else:
        # ── Inline text mode ──────────────────────────────────────────────────
        text = args.text

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
        for r in results[: args.top]:
            print(r["keyword"])


if __name__ == "__main__":
    main()
