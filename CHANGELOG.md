# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.6] — 2026-04-09

### Fixed
- CRLF line ending issue causing CI black check failure (added `.gitattributes`)
- `sentence-transformers` Tensor-to-numpy conversion in `_embed()` for mypy compatibility
- Docker workflow trigger conditions to depend on CI success

---

## [0.2.5] — 2026-04-09

### Added
- **Docker support** with multi-stage build for production deployment
- `Dockerfile` with builder and runtime stages
- `docker-compose.yml` for easy local development with persistent model cache
- `.dockerignore` to optimize build context
- **Docker Hub integration** via CI/CD workflows
- `docker.yml` workflow for automated builds on push to `main` and version tags
- `docker_cleanup.yml` workflow to retain only 4 latest Docker tags
- `docker_hub_description.yml` workflow to sync `README_DOCKER.md` to Docker Hub
- `README_DOCKER.md` — comprehensive Docker documentation
- `CONTRIBUTING.md` — full developer guide with setup, testing, and PR instructions
- Project icon (`docs/icon.svg`) for branding across README and landing page

### Changed
- Reorganized documentation: moved Docker instructions to `README_DOCKER.md`
- Moved developer guide to `CONTRIBUTING.md`
- Added Docker quick start section to `README.md`
- Updated landing page (`docs/index.html`) with Docker section and project icon
- `pages.yml` workflow now only triggers when `docs/index.html` changes
- Updated project structure documentation

---

## [0.2.0] — Previous Release

### Added
- `extract_file()` — keyword extraction directly from `.pdf`, `.txt`, `.md`
- `read_file()` and `file_info()` utilities for file handling
- `--file` / `-f` flag to the CLI for file-based extraction
- Interactive mode now offers text input or file path as input options
- `pypdf` added as optional dependency (`pip install semantic-keywords[files]`)
- Bumped `__version__` to `0.2.0`

---

## [0.1.0] — Initial Release

### Added
- `extract()` with MMR ranking for semantic keyword extraction
- Three model tiers: `fast`, `balanced`, `accurate`
- Auto model detection from HuggingFace cache
- Interactive CLI (`semkw`) with guided prompts
- Stdin pipe support
