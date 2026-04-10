# Internal Documentation — semantic-keywords

> This document covers project-specific automation, workflows, and decisions that aren't obvious from the code alone. Keep it updated when workflows or infrastructure change.

---

## Table of Contents

- [Workflow Execution Order](#workflow-execution-order)
- [Workflow Dependencies Graph](#workflow-dependencies-graph)
- [Trigger Conditions](#trigger-conditions)
- [Abort Behavior](#abort-behavior)
- [Secrets Required](#secrets-required)
- [Version Release Process](#version-release-process)
- [Docker Image Tagging Strategy](#docker-image-tagging-strategy)
- [Model Registry](#model-registry)
- [Optional Dependencies](#optional-dependencies)
- [Linting & Type Checking](#linting--type-checking)
- [Project Structure Decisions](#project-structure-decisions)
- [Local Development Tips](#local-development-tips)
- [Common Issues & Solutions](#common-issues--solutions)

---

## Workflow Execution Order

All GitHub Actions workflows are chained in a specific order to ensure quality gates pass before deployment. **CI is the gatekeeper** — if it fails, nothing else runs.

### Priority Order

| # | Workflow | File | Trigger | Blocks |
|---|----------|------|---------|--------|
| 1 | **CI** | `ci.yml` | Every push/PR to `main` | All other workflows |
| 2 | **Docker** | `docker.yml` | After CI success + Docker file changes | cleanup, description sync |
| 3 | **Docker Cleanup** | `docker_cleanup.yml` | After Docker success | — |
| 4 | **Docker Hub Description** | `docker_hub_description.yml` | After Docker success | — |
| 5 | **PyPI Publish** | `publish.yml` | Version tag (`v*.*.*`) | — |
| 6 | **Pages** | `pages.yml` | `docs/index.html` changes | — |

### Execution Flow

```
Push/PR to main
    │
    ▼
┌──────────┐
│   CI     │ ← Gatekeeper (lint, format, type-check)
└────┬─────┘
     │ ✅ success
     ▼
┌──────────────┐     ┌─────────────┐
│   Docker     │────▶│   PyPI      │
│ (if files    │     │ (on tag)    │
│  changed)    │     └─────────────┘
└──────┬───────┘
       │ ✅ success
       ▼
┌──────────────┐  ┌────────────────────┐
│   Cleanup    │  │  Hub Description   │
│  (4 tags)    │  │  (sync README)     │
└──────────────┘  └────────────────────┘

┌──────────────┐
│   Pages      │ ← Independent (only on index.html change)
└──────────────┘
```

---

## Workflow Dependencies Graph

### How `workflow_run` Works

Workflows use `workflow_run` to depend on other workflows' completion:

```yaml
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: ["main"]
```

The `if` condition ensures the dependent workflow only runs on success:

```yaml
if: ${{ github.event_name == 'workflow_run' && github.event.workflow_run.conclusion == 'success' }}
```

### Path Filters

To avoid unnecessary runs, workflows use `paths` filters:

**Docker workflow** triggers only when:
- `semantic_keywords/**` — package code changes
- `Dockerfile` — build configuration
- `docker-compose.yml` — compose configuration
- `.dockerignore` — build context changes
- `pyproject.toml` — dependency changes
- `requirements.txt` — pinned dependency changes

**Pages workflow** triggers only when:
- `docs/index.html` — landing page changes

---

## Trigger Conditions

### CI Workflow
- **Always runs** on push to `main` or PR targeting `main`
- No path filters — lints the entire codebase every time
- Fails fast if any linter or type checker errors

### Docker Workflow
- Runs after CI success **OR** on version tag push
- **Additional condition**: Checks commit message for "docker" or "Docker" keywords
- Path filters prevent runs on unrelated changes (docs, markdown, etc.)

### Docker Cleanup
- Only runs after Docker workflow success
- Manual dispatch available for ad-hoc cleanup
- Default: keeps 4 most recent tags

### Docker Hub Description
- Only runs after Docker workflow success
- Syncs `README_DOCKER.md` content to Docker Hub description
- Manual dispatch available for ad-hoc updates

### PyPI Publish
- **Primary trigger**: Version tag push (`v0.2.5`)
- Uses OIDC trusted publishing — no PyPI API token needed
- Environment protection: `pypi`

### Pages
- Only triggers when `docs/index.html` changes
- Independent from other workflows
- Deploys to GitHub Pages environment

---

## Abort Behavior

### Failure Scenarios

| Workflow Fails | Impact on Downstream |
|----------------|---------------------|
| **CI** | ❌ All other workflows abort |
| **Docker** | ❌ Cleanup & description sync abort |
| **PyPI Publish** | No impact on other workflows |
| **Pages** | No impact on other workflows |

### How Abort Works

GitHub Actions doesn't have explicit "abort" — instead, workflows use `if` conditions:

```yaml
if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

If the parent workflow fails, this condition evaluates to `false` and the job is **skipped** (not failed). This is intentional — a failed CI shouldn't block future successful runs.

### Why Not Use `needs`?

GitHub Actions `needs` keyword only works for jobs within the **same** workflow. For cross-workflow dependencies, `workflow_run` + `if` conditions are the only option.

---

## Secrets Required

All secrets are configured in **Settings → Secrets and variables → Actions**.

| Secret | Used By | Purpose |
|--------|---------|---------|
| `DOCKERHUB_USERNAME` | docker.yml, docker_cleanup.yml, docker_hub_description.yml | Docker Hub authentication |
| `DOCKERHUB_FA` | docker.yml, docker_cleanup.yml, docker_hub_description.yml | Docker Hub access token (personal access token) |

### PyPI Publishing

**No secret needed!** Uses [OIDC trusted publishing](https://docs.pypi.org/trusted-publishers/). Configure the trusted publisher in PyPI settings:
- Repository URL: `https://github.com/ronaldgosso/semantic-keywords`
- Workflow: `publish.yml`
- Environment: `pypi`

---

## Version Release Process

### Step-by-Step

```bash
# 1. Update version in pyproject.toml and semantic_keywords/__init__.py
#    Current version: 0.2.5

# 2. Update CHANGELOG.md with new version entry

# 3. Update version in docs/index.html (nav badge + footer)

# 4. Commit changes
git add .
git commit -m "chore: bump version to 0.2.6"

# 5. Tag and push
git tag v0.2.6
git push && git push --tags
```

### What Happens After Push

1. **CI** runs immediately — must pass
2. **PyPI Publish** triggers on the tag push
3. **Docker** builds the image (if CI passed)
4. **Docker Cleanup** removes old tags (keeps 4)
5. **Docker Hub Description** syncs `README_DOCKER.md`

### Version Tagging Convention

- Format: `vMAJOR.MINOR.PATCH` (e.g., `v0.2.5`)
- Semantic versioning is enforced
- PyPI workflow only triggers on `v*.*.*` pattern

---

## Docker Image Tagging Strategy

### Tags Generated Per Build

The `docker/metadata-action` generates these tags automatically:

| Tag | Example | When |
|-----|---------|------|
| `main` | `ronaldgosso/semantic-keywords:main` | Push to main branch |
| `v0.2.5` | `ronaldgosso/semantic-keywords:v0.2.5` | Version tag |
| `0.2` | `ronaldgosso/semantic-keywords:0.2` | Version tag (major.minor) |
| `0` | `ronaldgosso/semantic-keywords:0` | Version tag (major only) |
| `<sha>` | `ronaldgosso/semantic-keywords:abc1234` | Every build |

### Why Keep Only 4 Tags?

Docker Hub has storage limits and old images accumulate quickly. Keeping 4 most recent tags ensures:
- Latest version is available
- Previous 3 versions are accessible for rollback
- Old dev/SHA builds are cleaned up automatically

### Multi-Platform Support

Images are built for:
- `linux/amd64` (most servers, desktops)
- `linux/arm64` (Apple Silicon, ARM servers)

Uses Docker Buildx with GitHub Actions cache for faster builds.

---

## Model Registry

### How Model Detection Works

The package auto-detects downloaded models from HuggingFace cache:

```python
# semantic_keywords/extractor.py
MODEL_REGISTRY = {
    "fast":     {"hf_name": "all-MiniLM-L6-v2",  "size": "90MB",  "note": "..."},
    "balanced": {"hf_name": "all-MiniLM-L12-v2", "size": "120MB", "note": "..."},
    "accurate": {"hf_name": "all-mpnet-base-v2",  "size": "420MB", "note": "..."},
}
```

### Adding a New Model

1. Add entry to `MODEL_REGISTRY` in `extractor.py`
2. That's it — CLI menu, API, and detection all pick it up automatically

### Model Storage Location

- **HuggingFace cache**: `~/.cache/huggingface/`
- **Docker container**: `/cache` (mapped to `TRANSFORMERS_CACHE` env var)
- **Docker volume**: `model-cache` in docker-compose.yml

---

## Optional Dependencies

### Why Optional?

PDF support requires `pypdf` (~1MB), but most users only need text extraction. Making it optional keeps the base install lightweight.

### Install Variants

```bash
# Base — text extraction only
pip install semantic-keywords

# With PDF support
pip install "semantic-keywords[files]"

# For development
pip install -e ".[dev]"
```

### What `[files]` Includes

- `pypdf>=4.0` — PDF parsing
- Required for `.pdf` file support in `extract_file()` and `read_file()`

### What `[dev]` Includes

- `ruff>=0.4` — linting
- `mypy>=1.9` — type checking
- `black>=24.0` — formatting
- `build>=1.0` — package building
- `twine>=5.0` — PyPI uploading
- `pypdf>=4.0` — PDF support

---

## Linting & Type Checking

### Tools & Order

```bash
# 1. Ruff — lint (fast, catches most issues)
ruff check semantic_keywords/

# 2. Ruff — import sorting
ruff check --select I semantic_keywords/

# 3. Black — formatting
black --check semantic_keywords/

# 4. Mypy — type checking (slowest, most thorough)
mypy semantic_keywords/
```

### Configuration

All configured in `pyproject.toml`:

```toml
[tool.ruff]
line-length    = 100
target-version = "py39"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "W"]
ignore = ["E501"]

[tool.mypy]
python_version         = "3.10"
warn_return_any        = true
warn_unused_configs    = true
ignore_missing_imports = true
strict                 = false

[tool.black]
line-length    = 100
target-version = ["py39"]
```

### Known Mypy Issue

`extractor.py:231` has a pre-existing `no-any-return` error:
```
error: Returning Any from function declared to return "ndarray[...]"
```
This is from `sentence-transformers` returning untyped numpy arrays. Safe to ignore for now — fixing would require upstream type stubs.

---

## Project Structure Decisions

### Documentation Split

| File | Audience | Content |
|------|----------|---------|
| `README.md` | End users | Installation, quick start, API reference, configuration |
| `README_DOCKER.md` | DevOps / Docker users | Docker setup, compose, production deployment |
| `CONTRIBUTING.md` | Developers | Fork setup, testing, PR process, workflows |
| `INTERNAL_DOC.md` | Maintainers | Workflow automation, secrets, release process |
| `CHANGELOG.md` | Everyone | Version history and changes |
| `docs/index.html` | Website visitors | Polished landing page |

### Why Multiple Docker Workflows?

Instead of one monolithic workflow, we split concerns:
- **docker.yml**: Build and push — runs only when needed
- **docker_cleanup.yml**: Tag cleanup — independent schedule
- **docker_hub_description.yml**: Sync docs — can run ad-hoc

Benefits:
- Faster feedback (parallel when possible)
- Easier debugging (isolated failures)
- Flexible triggers (different conditions per workflow)

---

## Local Development Tips

### Editable Install

```bash
pip install -e .
```

The `semkw` command now points to your source files — any edit is reflected immediately.

### Testing Without Full Install

```bash
# Run the CLI directly without installing
python -m semantic_keywords.cli "test text"

# Run the test suite
python test_extractor.py
```

### Docker Development

```bash
# Build and run in one command
docker compose run --rm semkw "test text"

# Mount local code for live development
docker compose -f docker-compose.yml run --rm semkw bash
```

### Model Downloads

```bash
# Download default model
python download_model.py

# Or via Python
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# List downloaded models
semkw --list-models
```

---

## Common Issues & Solutions

### CI Fails But Locally Passes

**Cause**: Different Python version or dependency versions.
**Fix**: Ensure local Python matches CI (`3.11`) and run `pip install -e ".[dev]"`.

### Docker Build Fails

**Cause**: Missing files in build context (check `.dockerignore`).
**Fix**: Verify `Dockerfile` copies all necessary files. Check `.dockerignore` isn't excluding needed files.

### PyPI Publish Fails

**Cause**: Missing trusted publisher configuration.
**Fix**: Go to PyPI → Account Settings → Trusted Publishers → Add new publisher with:
  - GitHub repository: `ronaldgosso/semantic-keywords`
  - Workflow name: `publish.yml`
  - Environment: `pypi`

### Workflow Doesn't Trigger

**Cause**: Path filters blocking execution.
**Fix**: Check if changed files match the `paths` filter in the workflow YAML. Use `git diff --name-only HEAD~1` to see what changed.

### Docker Image Too Large

**Cause**: Multi-stage build not working correctly.
**Fix**: Ensure `COPY --from=builder /opt/venv /opt/venv` is present and `target: runtime` is set in build step.

### Mypy Timeout

**Cause**: Type checking sentence-transformers dependencies is slow.
**Fix**: This is expected. The timeout in CI is 120s which is usually enough. If it times out consistently, consider adding `# type: ignore` to problematic imports.

---

## Future Improvements

- [ ] Add integration tests for CLI flags
- [ ] Set up Dependabot for dependency updates
- [ ] Add code coverage reporting
- [ ] Consider adding GPU support for Docker image
- [ ] Add performance benchmarks to CI
- [ ] Set up automated releases (bump version + tag + changelog)

---

*Last updated: 2026-04-09 · v0.2.5*
