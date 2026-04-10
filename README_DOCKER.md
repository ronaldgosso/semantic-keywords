<div align="center">

# Docker — semantic-keywords

Run semantic-keywords in Docker containers for production, CI/CD, or isolated environments.

</div>

---

## Table of contents

- [Quick start](#quick-start)
- [Pull from Docker Hub](#pull-from-docker-hub)
- [Build locally](#build-locally)
- [Docker Compose](#docker-compose)
- [Persistent model cache](#persistent-model-cache)
- [Dockerfile structure](#dockerfile-structure)
- [Environment variables](#environment-variables)
- [Volumes](#volumes)
- [Multi-platform builds](#multi-platform-builds)
- [Troubleshooting](#troubleshooting)

---

## Quick start

```bash
# Inline text
docker run --rm ronaldgosso/semantic-keywords "Tanzania fintech mobile money"

# With scores
docker run --rm ronaldgosso/semantic-keywords "climate change arctic" --scores -n 8

# Extract from a file (mount the file directory)
docker run --rm -v ./documents:/data ronaldgosso/semantic-keywords --file /data/report.pdf
```

---

## Pull from Docker Hub

```bash
docker pull ronaldgosso/semantic-keywords
```

Images are automatically built and pushed on every push to `main` and version tags.

| Tag | Description |
|---|---|
| `latest` | Latest stable release |
| `v0.x.x` | Specific version |
| `main` | Latest commit on main branch |
| `<sha>` | Specific commit SHA |

---

## Build locally

```bash
# Build the image
docker build -t semantic-keywords .

# Build a specific target
docker build --target runtime -t semantic-keywords:runtime .

# Run the image
docker run --rm semantic-keywords "your text here"
```

---

## Docker Compose

The included `docker-compose.yml` provides a ready-to-use configuration:

```bash
# Create a data directory for your files
mkdir -p data

# Run with inline text
docker compose run --rm semkw "your text here"

# Extract from a file
cp report.pdf data/
docker compose run --rm semkw --file /data/report.pdf --scores

# Interactive mode
docker compose run --rm semkw
```

### docker-compose.yml structure

| Component | Purpose |
|---|---|
| `semkw` service | Main container with `semkw` CLI |
| `./data:/data` volume | Mount local files for extraction |
| `model-cache` volume | Persist downloaded models across runs |

---

## Persistent model cache

The compose file includes a `model-cache` volume so the embedding model is downloaded only once:

```bash
# First run — downloads the model (~90 MB)
docker compose run --rm semkw "test text"

# Subsequent runs — uses cached model, much faster
docker compose run --rm semkw --file /data/notes.txt
```

To clear the cache:

```bash
docker compose down -v
```

---

## Dockerfile structure

The Dockerfile uses a **multi-stage build** to minimize image size:

| Stage | Purpose |
|---|---|
| `builder` | Installs Python, dependencies, and the package |
| `runtime` | Minimal image with only the installed package |

```dockerfile
# Builder stage
FROM python:3.11-slim AS builder
# ... install dependencies

# Runtime stage
FROM python:3.11-slim AS runtime
# ... copy venv, set entrypoint
```

This produces a smaller final image by excluding build tools and intermediate layers.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `TRANSFORMERS_CACHE` | `/cache` | Path for downloaded models |
| `SENTENCE_TRANSFORMERS_HOME` | `/cache` | Alternative model cache path |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout/stderr |
| `PYTHONDONTWRITEBYTECODE` | `1` | Disable `.pyc` files |

Customize in `docker-compose.yml` or with `-e`:

```bash
docker run --rm -e TRANSFORMERS_CACHE=/custom/path semantic-keywords "text"
```

---

## Volumes

| Mount point | Purpose |
|---|---|
| `/data` | Input files for extraction |
| `/cache` | Model download cache |

### Example with custom mounts

```bash
docker run --rm \
  -v ./my-documents:/data \
  -v ./my-model-cache:/cache \
  ronaldgosso/semantic-keywords \
  --file /data/report.pdf --scores -n 10
```

---

## Multi-platform builds

The CI workflow builds for both `linux/amd64` and `linux/arm64`. For local multi-platform builds:

```bash
# Create a builder with cross-platform support
docker buildx create --use --name multi-platform

# Build for both platforms
docker buildx build --platform linux/amd64,linux/arm64 -t semantic-keywords .
```

---

## Troubleshooting

### Model download fails

Ensure the container has internet access and the `/cache` directory is writable:

```bash
docker run --rm -v ./cache:/cache semantic-keywords --list-models
```

### File not found

Verify the mount path matches the path passed to `--file`:

```bash
# Wrong — file mounted to /data but using relative path
docker run -v ./docs:/data semantic-keywords --file report.pdf

# Correct — use the mount point path
docker run -v ./docs:/data semantic-keywords --file /data/report.pdf
```

### Interactive mode doesn't work

Ensure `stdin_open` and `tty` are enabled:

```bash
docker run --rm -it semantic-keywords
# or with compose
docker compose run semkw
```

---

## CI/CD pipeline

The `.github/workflows/docker.yml` workflow automatically:

1. Triggers on pushes to `main` or `v*` tags
2. Builds for `linux/amd64` and `linux/arm64`
3. Pushes to Docker Hub with semantic tags
4. Uses GitHub Actions cache for faster builds

### Required secrets

| Secret | Purpose |
|---|---|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_FA` | Docker Hub access token |

Set these in **Settings → Secrets and variables → Actions**.

---

## Links

| Resource | URL |
|---|---|
| Main README | [README.md](../README.md) |
| Contributing guide | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| Docker Hub | https://hub.docker.com/r/ronaldgosso/semantic-keywords |
| GitHub repository | https://github.com/ronaldgosso/semantic-keywords |

---

## License

MIT © [Ronald Isack Gosso](https://github.com/ronaldgosso)
