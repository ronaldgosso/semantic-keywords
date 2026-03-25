# semantic-keywords

[![CI](https://github.com/ronaldgosso/semantic-keywords/actions/workflows/ci.yml/badge.svg)](https://github.com/ronaldgosso/semantic-keywords/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/semantic-keywords.svg)](https://pypi.org/project/semantic-keywords/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

AI-powered semantic keyword extraction for Python.

Uses sentence embeddings (`all-MiniLM-L6-v2` by default) and Maximal Marginal
Relevance (MMR) to return keywords that are both **relevant** and **diverse** —
not just statistically frequent.

→ **[Full docs & demo](https://ronaldgosso.github.io/semantic-keywords)**

---

## Install

```bash
pip install semantic-keywords
```

On first run, download at least one model:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

## Quick start

```python
from semantic_keywords import extract

results = extract("Tanzania is a hub for mobile money and fintech startups.")

for r in results:
    print(r["score"], r["keyword"])
# 0.5134  mobile money
# 0.4901  fintech startups
# 0.4710  east africa
```

## CLI

```bash
# Interactive guided mode
semkw

# Inline
semkw "Tanzania fintech mobile money" --top 5 --scores

# Pipe
echo "neural networks deep learning transformers" | semkw -n 3

# Show downloaded models
semkw --list-models
```

## Parameters

| Parameter   | Default  | Description                                      |
|-------------|----------|--------------------------------------------------|
| `top_n`     | `5`      | Maximum keywords to return                       |
| `min_score` | `0.20`   | Minimum cosine similarity threshold (0.0–1.0)    |
| `diversity` | `0.7`    | MMR balance: `0.0` = most relevant, `1.0` = most varied |
| `model`     | `"fast"` | `"fast"` · `"balanced"` · `"accurate"` · any HF model name |

## Model options

| Alias      | Model                 | Size   | Note                     |
|------------|-----------------------|--------|--------------------------|
| `fast`     | all-MiniLM-L6-v2      | 90 MB  | Default, fastest         |
| `balanced` | all-MiniLM-L12-v2     | 120 MB | Slightly better accuracy |
| `accurate` | all-mpnet-base-v2     | 420 MB | Best quality, slower CPU |

All models run **fully offline** after the first download.

## License

MIT © [Ronald Isack Gosso](https://github.com/ronaldgosso)