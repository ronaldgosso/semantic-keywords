<div align="center">

<h1>semantic-keywords</h1>

<p><em>AI-powered semantic keyword extraction — offline, fast, and actually useful.</em></p>

[![CI](https://github.com/ronaldgosso/semantic-keywords/actions/workflows/ci.yml/badge.svg)](https://github.com/ronaldgosso/semantic-keywords/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/semantic-keywords.svg?color=7c6af7)](https://pypi.org/project/semantic-keywords/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-3ecfb2.svg)](https://opensource.org/licenses/MIT)
 [![Downloads](https://img.shields.io/pypi/dm/semantic-keywords.svg)](https://pypi.org/project/semantic-keywords/)

<br/>

**[📖 Landing Page](https://ronaldgosso.github.io/semantic-keywords)** &nbsp;·&nbsp;
**[📦 PyPI](https://pypi.org/project/semantic-keywords/)** &nbsp;·&nbsp;
**[🐛 Issues](https://github.com/ronaldgosso/semantic-keywords/issues)**

<br/>

</div>

---

TF-IDF counts words. `semantic-keywords` understands **meaning**.

It uses sentence embeddings (`all-MiniLM-L6-v2` by default) and **Maximal Marginal Relevance (MMR)** to return keywords that are both *relevant* and *diverse* — not just the most frequent phrases. Works fully offline after a one-time model download. No API key. No rate limits.

```
Input  → "Tanzania is a hub for mobile money and fintech startups in East Africa."

Output → mobile money       0.5134  ████████████████░░░░░░░░
         fintech startups   0.4901  ██████████████░░░░░░░░░░
         east africa        0.4710  █████████████░░░░░░░░░░░
         financial access   0.4502  ████████████░░░░░░░░░░░░
         agricultural tools 0.4388  ████████████░░░░░░░░░░░░
```

---

## Table of contents

- [Install](#install)
- [Quick start](#quick-start)
- [File extraction (PDF, TXT, MD)](#file-extraction)
- [CLI reference](#cli-reference)
- [Python API reference](#python-api-reference)
- [Model options](#model-options)
- [Configuration](#configuration)
- [Project structure](#project-structure)
- [Changelog](#changelog)
- [Contributing](#contributing)

---

## Install

```bash
pip install semantic-keywords
```

**With PDF support:**

```bash
pip install "semantic-keywords[files]"
```

**Download a model** (one-time, then fully offline):

```bash
# Quickest — 90 MB, works great for most use cases
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

Or use the interactive downloader bundled with the repo:

```bash
python download_model.py
```

---

## Quick start

### Python API

```python
from semantic_keywords import extract

# Basic — returns top 5 keywords
results = extract("Tanzania is a hub for mobile money and fintech startups.")

for r in results:
    print(r["score"], r["keyword"])

# 0.5134  mobile money
# 0.4901  fintech startups
# 0.4710  east africa
```

```python
# Full control
results = extract(
    text      = "your paragraph or document here",
    top_n     = 10,          # how many keywords to return
    min_score = 0.25,        # only keep keywords above this similarity score
    diversity = 0.7,         # 0.0 = most relevant, 1.0 = most varied
    model     = "balanced",  # "fast" | "balanced" | "accurate"
)
```

### CLI

```bash
# Interactive guided mode — prompts you for text or a file path
semkw

# Inline text
semkw "Tanzania fintech mobile money startups"

# Top N with score table
semkw "climate change arctic ice melting" --top 8 --scores

# Pipe from stdin
echo "neural networks deep learning transformers" | semkw -n 3
```

---

## File extraction

Extract keywords directly from `.pdf`, `.txt`, and `.md` files.

### Python API

```python
from semantic_keywords import extract_file

# One-call file extraction
result = extract_file("annual_report.pdf", top_n=10)

print(result["file"])      # "annual_report.pdf"
print(result["size_kb"])   # 284.1
print(result["words"])     # 6203

for kw in result["keywords"]:
    print(kw["score"], kw["keyword"])
```

```python
# Two-step: read then extract separately
from semantic_keywords import read_file, extract

text    = read_file("notes.txt")        # returns raw string
results = extract(text, top_n=5)
```

`extract_file()` returns:

| Key | Type | Description |
|---|---|---|
| `file` | `str` | Filename (not full path) |
| `size_kb` | `float` | File size in KB |
| `words` | `int` | Word count of extracted text |
| `model` | `str` | Model alias used |
| `keywords` | `list[dict]` | `[{"keyword": str, "score": float}, ...]` |

### CLI

```bash
# Extract from a PDF
semkw --file report.pdf

# Top 10 with scores
semkw --file report.pdf --top 10 --scores

# Drag and drop the path in interactive mode
semkw
# → choose [2] Load from file
# → paste or drag the file path
```

### PDF requirements

PDF support requires `pypdf`:

```bash
pip install pypdf
# or
pip install "semantic-keywords[files]"
```

> **Note:** Image-only / scanned PDFs contain no extractable text. Run them through OCR (e.g. Adobe Acrobat, Tesseract) before using this package. Password-protected PDFs must be decrypted first.

---

## CLI reference

```
semkw [TEXT] [OPTIONS]
```

| Argument / Flag | Default | Description |
|---|---|---|
| `TEXT` | — | Inline text to extract from. Omit for interactive mode. |
| `--file`, `-f PATH` | — | Path to a `.pdf`, `.txt`, or `.md` file. |
| `--top`, `-n N` | `5` | Maximum keywords to return. |
| `--model`, `-m MODEL` | auto | `fast` · `balanced` · `accurate` |
| `--min-score FLOAT` | `0.20` | Minimum cosine similarity threshold (0.0–1.0). |
| `--diversity FLOAT` | `0.70` | MMR balance: `0.0` = most relevant, `1.0` = most varied. |
| `--scores` | off | Print ranked score table instead of plain list. |
| `--list-models` | — | Show all models and download status, then exit. |

**Examples:**

```bash
semkw                                              # interactive guided mode
semkw "your text here"                             # inline, default top 5
semkw "your text here" -n 3                        # top 3
semkw "your text here" --scores                    # with score table
semkw --file report.pdf                            # from PDF
semkw --file report.pdf -n 10 --model accurate     # PDF, top 10, best model
semkw --file notes.txt --scores                    # txt with scores
semkw --list-models                                # show downloaded models
echo "deep learning transformers" | semkw -n 3     # pipe
```

---

## Python API reference

### Google Colab Example [Link](https://colab.research.google.com/drive/1KTsJmRSWh4B_P6d76cmeyIr4O_Igmqv4?usp=sharing)

### `extract(text, **kwargs) → list[dict]`

```python
from semantic_keywords import extract

results = extract(
    text      : str,            # input document
    top_n     : int   = 5,      # max keywords to return
    min_score : float = 0.20,   # minimum cosine similarity (0.0–1.0)
    max_words : int   = 3,      # max words per keyword phrase
    model     : str   = "fast", # model alias or HuggingFace model name
    diversity : float = 0.7,    # MMR diversity factor (0.0–1.0)
)
# → [{"keyword": "mobile money", "score": 0.5134}, ...]
```

### `extract_file(file_path, **kwargs) → dict`

```python
from semantic_keywords import extract_file

result = extract_file(
    file_path : str | Path,     # path to .pdf, .txt, or .md
    top_n     : int   = 5,
    min_score : float = 0.20,
    max_words : int   = 3,
    model     : str   = "fast",
    diversity : float = 0.7,
)
# → {"file": "report.pdf", "size_kb": 142.3, "words": 4821,
#    "model": "fast", "keywords": [...]}
```

### `read_file(file_path) → str`

```python
from semantic_keywords import read_file

text = read_file("report.pdf")   # raw extracted text string
```

### `detect_available_models() → dict`

```python
from semantic_keywords import detect_available_models

available = detect_available_models()
# → {"fast": {"hf_name": "all-MiniLM-L6-v2", "size": "90MB", ...}}
```

### `list_models() → dict`

```python
from semantic_keywords import list_models

all_models = list_models()
# → full MODEL_REGISTRY dict including models not yet downloaded
```

---

## Model options

| Alias | HuggingFace model | Size | Speed | Best for |
|---|---|---|---|---|
| `fast` *(default)* | `all-MiniLM-L6-v2` | 90 MB | fastest | Most use cases |
| `balanced` | `all-MiniLM-L12-v2` | 120 MB | medium | Better accuracy |
| `accurate` | `all-mpnet-base-v2` | 420 MB | slowest | Research / high precision |
| *(custom)* | any HuggingFace model name | varies | varies | Advanced users |

All models run **fully offline** after the first download. The package auto-detects which models are present and shows a menu when multiple are available.

**Download additional models:**

```bash
python download_model.py
```

**Use a custom HuggingFace model:**

```python
results = extract("your text", model="BAAI/bge-small-en-v1.5")
```

---

## Configuration

### `min_score` — precision vs recall

| Value | Effect |
|---|---|
| `0.10` | Very broad — returns many keywords, some loosely related |
| `0.20` | Default — balanced precision |
| `0.30` | Strict — only highly relevant keywords |
| `0.40+` | Very strict — few but precise keywords |

### `diversity` — MMR balance

| Value | Effect |
|---|---|
| `0.0` | Pure relevance — top keywords may paraphrase each other |
| `0.7` | Default — relevant and varied |
| `1.0` | Pure diversity — maximally varied, may miss the most relevant phrase |

### `max_words` — phrase length

| Value | Effect |
|---|---|
| `1` | Single words only |
| `2` | Up to bigrams (e.g. "mobile money") |
| `3` | Up to trigrams — default, catches most meaningful phrases |

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the full developer guide, including:

- Fork and local setup instructions
- Running tests and linters
- Making a release
- Adding new models
- Docker development workflow

### Quick contributor setup

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/<your-username>/semantic-keywords.git
cd semantic-keywords

# Create and activate a virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Download a model
python download_model.py
```

---

## Project structure

```
semantic-keywords/
├── semantic_keywords/          # installable package
│   ├── __init__.py             # public API surface
│   ├── extractor.py            # embeddings, MMR, model registry
│   ├── reader.py               # PDF / txt / md file reading
│   ├── file_api.py             # extract_file() — reader + extractor combined
│   └── cli.py                  # semkw CLI entry point
├── docs/
│   └── index.html              # GitHub Pages landing page
├── .github/
│   └── workflows/
│       ├── ci.yml              # lint on every push
│       ├── publish.yml         # publish to PyPI on version tag
│       ├── docker.yml          # build & push Docker image
│       └── pages.yml           # deploy docs on push to main
├── pyproject.toml              # package metadata + tool config
├── Dockerfile                  # multi-stage Docker build
├── docker-compose.yml          # Docker Compose for local usage
├── .dockerignore               # files to exclude from Docker build
├── README.md                   # this file — user documentation
├── README_DOCKER.md            # Docker-specific instructions
├── CONTRIBUTING.md             # developer guide
├── test_extractor.py           # test suite + interactive demo
└── download_model.py           # interactive model downloader
```

---

## Changelog

### v0.2.0
- Added `extract_file()` — keyword extraction directly from `.pdf`, `.txt`, `.md`
- Added `read_file()` and `file_info()` utilities
- Added `--file` / `-f` flag to the CLI
- Interactive mode now offers text input or file path as input options
- `pypdf` added as optional dependency (`pip install semantic-keywords[files]`)
- Bumped `__version__` to `0.2.0`

### v0.1.0
- Initial release
- `extract()` with MMR ranking
- Three model tiers: `fast`, `balanced`, `accurate`
- Auto model detection from HuggingFace cache
- Interactive CLI (`semkw`) with guided prompts
- Stdin pipe support

---

## Links

| Resource | URL |
|---|---|
| Landing page | https://ronaldgosso.github.io/semantic-keywords |
| PyPI | https://pypi.org/project/semantic-keywords/ |
| GitHub | https://github.com/ronaldgosso/semantic-keywords |
| Issues | https://github.com/ronaldgosso/semantic-keywords/issues |
| CI status | https://github.com/ronaldgosso/semantic-keywords/actions |
| Contributing guide | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Docker guide | [README_DOCKER.md](README_DOCKER.md) |

---

## License

MIT © [Ronald Isack Gosso](https://github.com/ronaldgosso)
