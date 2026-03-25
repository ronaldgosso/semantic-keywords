# semantic-keywords

AI-powered semantic keyword extraction for Python.

Uses sentence embeddings (`all-MiniLM-L6-v2` by default) and
Maximal Marginal Relevance (MMR) to extract keywords that are
both relevant and diverse — not just statistically frequent.

## Install
```bash
pip install semantic-keywords
```

## Quick start
```python
from semantic_keywords import extract

results = extract("Tanzania is a hub for mobile money and fintech startups.")
for r in results:
    print(r["score"], r["keyword"])
```

## CLI
```bash
semkw "Tanzania is a hub for mobile money fintech"
semkw "climate change arctic ice" --top 8 --model accurate --scores
semkw --list-models
```

## Model options

| Alias      | Model                   | Size  | Note                        |
|------------|-------------------------|-------|-----------------------------|
| `fast`     | all-MiniLM-L6-v2        | 90MB  | default, fastest            |
| `balanced` | all-MiniLM-L12-v2       | 120MB | slightly better accuracy    |
| `accurate` | all-mpnet-base-v2       | 420MB | best quality, slower on CPU |

## Parameters

| Parameter   | Default | Description                              |
|-------------|---------|------------------------------------------|
| `top_n`     | 5       | Maximum keywords to return               |
| `min_score` | 0.20    | Minimum cosine similarity threshold      |
| `diversity` | 0.7     | MMR balance: 0 = relevant, 1 = diverse   |
| `model`     | "fast"  | Which embedding model to use             |

## License

MIT