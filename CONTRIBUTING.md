# Contributing to semantic-keywords

Thank you for your interest in contributing! This guide covers everything you need to set up the project locally, make changes, and submit a pull request.

---

## Table of contents

- [Fork and set up locally](#fork-and-set-up-locally)
- [Running the CLI locally](#running-the-cli-locally)
- [Run the test suite](#run-the-test-suite)
- [Linting and formatting](#linting-and-formatting)
- [Making a release](#making-a-release)
- [GitHub Actions workflows](#github-actions-workflows)
- [Adding a new model](#adding-a-new-model)
- [Building with Docker](#building-with-docker)
- [Opening a pull request](#opening-a-pull-request)
- [Code of conduct](#code-of-conduct)

---

## Fork and set up locally

```bash
# 1. Fork on GitHub, then clone your fork
git clone https://github.com/<your-username>/semantic-keywords.git
cd semantic-keywords

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install in editable mode with all dev dependencies
pip install -e ".[dev]"

# 4. Download at least one model
python download_model.py
```

---

## Running the CLI locally

After `pip install -e .`, the `semkw` command is live and points at your source files — any edit you make is reflected immediately without reinstalling.

```bash
semkw "your test text here" --scores
semkw --file path/to/test.pdf -n 10
semkw --list-models
```

---

## Run the test suite

```bash
python test_extractor.py
```

This detects downloaded models, prompts you to pick one, runs all automated tests (text + file extraction + edge cases + error handling), then drops into a live interactive demo.

---

## Linting and formatting

```bash
# Check for issues
ruff check semantic_keywords/
black --check semantic_keywords/
mypy semantic_keywords/

# Auto-fix what can be fixed automatically
ruff check --fix semantic_keywords/
black semantic_keywords/
```

All three must pass before opening a pull request. The CI workflow runs them automatically on every push.

---

## Making a release

```bash
# Bump version in pyproject.toml and __init__.py
# Then tag and push — the publish workflow fires automatically
git add .
git commit -m "release: v0.2.0"
git tag v0.2.0
git push && git push --tags
```

The `publish.yml` workflow builds the wheel and uploads to PyPI using OIDC trusted publishing — no API token needed.

---

## GitHub Actions workflows

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | Every push / PR to `main` | ruff + black + mypy |
| `publish.yml` | Push a `v*.*.*` tag | Build wheel + upload to PyPI |
| `docker.yml` | Push to `main` or `v*` tag | Build & push Docker image to Docker Hub |
| `pages.yml` | Every push to `main` | Deploy `docs/` to GitHub Pages |

---

## Adding a new model

Open `semantic_keywords/extractor.py` and add an entry to `MODEL_REGISTRY`:

```python
MODEL_REGISTRY: dict[str, dict[str, str]] = {
    "fast":     {"hf_name": "all-MiniLM-L6-v2",  "size": "90MB",  "note": "..."},
    "balanced": {"hf_name": "all-MiniLM-L12-v2", "size": "120MB", "note": "..."},
    "accurate": {"hf_name": "all-mpnet-base-v2",  "size": "420MB", "note": "..."},
    "your-alias": {"hf_name": "org/model-name",   "size": "???MB", "note": "..."},  # ← add here
}
```

No other changes needed — the CLI menu, detection logic, and API all pick it up automatically.

---

## Building with Docker

You can also develop and test inside a Docker container. See [README_DOCKER.md](README_DOCKER.md) for full details.

### Quick start

```bash
# Build the image
docker build -t semantic-keywords .

# Run with docker compose
mkdir -p data
docker compose run --rm semkw "your text here"

# Extract from a file
cp report.pdf data/
docker compose run --rm semkw --file /data/report.pdf --scores
```

### Persistent model cache

The compose file includes a `model-cache` volume so the embedding model is downloaded only once:

```bash
# First run — downloads the model (~90 MB)
docker compose run --rm semkw "test text"

# Subsequent runs — uses cached model, much faster
docker compose run --rm semkw --file /data/notes.txt
```

---

## Opening a pull request

1. **Fork the repo** on GitHub
2. **Create a feature branch**: `git checkout -b feat/your-feature`
3. **Make your changes** and ensure all linters pass
4. **Open a pull request** against `main`

Please **open an issue first** for significant changes so we can discuss the approach.

### PR checklist

- [ ] Tests pass (`python test_extractor.py`)
- [ ] Linters pass (`ruff check`, `black --check`, `mypy`)
- [ ] Updated documentation if behavior changes
- [ ] Added tests for new features
- [ ] Commit messages follow conventional format

### Commit message style

We use conventional commit messages:

```
feat: add new feature
fix: resolve a bug
docs: update documentation
chore: maintenance tasks
refactor: code cleanup without behavior changes
test: add or update tests
```

---

## Code of conduct

Be respectful, constructive, and inclusive. Treat all contributors with kindness and focus discussions on the technical merits of proposals.

---

## Links

| Resource | URL |
|---|---|
| Main README | [README.md](README.md) |
| Docker guide | [README_DOCKER.md](README_DOCKER.md) |
| Issues | https://github.com/ronaldgosso/semantic-keywords/issues |
| Discussions | https://github.com/ronaldgosso/semantic-keywords/discussions |

---

## License

MIT © [Ronald Isack Gosso](https://github.com/ronaldgosso)
