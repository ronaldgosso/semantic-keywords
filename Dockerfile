# syntax=docker/dockerfile:1

###############################################################################
# Builder stage — install dependencies and build the package
###############################################################################
FROM python:3.11-slim AS builder

WORKDIR /build

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (better layer caching)
COPY requirements.txt pyproject.toml ./

# Install the package and all dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[files]"

###############################################################################
# Runtime stage — minimal image with only what's needed to run
###############################################################################
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    TRANSFORMERS_CACHE=/cache \
    SENTENCE_TRANSFORMERS_HOME=/cache

# Copy the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Install curl for health checks (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create cache directory for model downloads
RUN mkdir -p /cache && chmod 777 /cache

# Create a volume mount point for input files
VOLUME ["/data"]

# Copy the package source (for editable install access)
COPY semantic_keywords/ ./semantic_keywords/

# Default command runs the CLI in interactive mode
ENTRYPOINT ["semkw"]
CMD ["--help"]
