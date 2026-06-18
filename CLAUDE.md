# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Obsidian File API** is a FastAPI server that provides HTTP endpoints for reading, writing, and listing files in an Obsidian vault. It handles YAML frontmatter parsing and supports filtering hidden files/directories.

**Tech Stack**: Python 3.13, FastAPI, pydantic, pyyaml, loguru, pytest

## Architecture

### Core Components

- **`app/main.py`** — FastAPI application entry point. Sets up logging and includes the router under `/v1/files` prefix.
- **`app/router.py`** — Defines all HTTP endpoints (`GET /`, `/read`, `POST /write`, `PATCH /write`). Handles request validation, error responses, and logging.
- **`app/file_handler.py`** — Contains `FileHandler` class, the core business logic for all file operations (list, read, write, update, frontmatter extraction). Uses dependency injection (`get_file_handler`).
- **`app/exception.py`** — `CustomError` exception class with status codes and response formatting.
- **`app/env.py`** — Environment configuration (reads `BASE_DIR` env var; defaults to app directory).

### Key Patterns

- **Dependency Injection**: FastAPI `Depends()` pattern used in router endpoints to inject `FileHandler`.
- **Markdown + YAML Frontmatter**: Files must be `.md` format. Frontmatter is parsed via `---` delimiters using `yaml.safe_load()`.
- **Path Validation**: All paths must be relative (not absolute) and within the configured `BASE_DIR`. Hidden files/dirs (starting with `.`) are filtered.
- **Error Handling**: Specific `CustomError` exceptions with HTTP status codes caught in router and returned as JSON responses.

## Development

### Installation & Setup

```bash
# Install dependencies (includes dev tools)
uv sync --locked --all-extras --dev

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### Running the App

```bash
# Local development server (auto-reload)
uv run fastapi run app/main.py

# Docker (with sample vault in scratch/vault)
docker-compose up
```

The app serves on `http://localhost:8000` locally or `http://localhost:8005` in Docker.

### Testing

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app

# Run a specific test file or test
uv run pytest app/test/test_main.py
uv run pytest app/test/test_main.py::test_function_name
```

Tests use pytest fixtures (in `app/test/conftest.py`):
- `temp_dir` — temporary directory for test files
- `setup_temp_dir_content` — helper to create test files with content
- `client` — TestClient with `FileHandler` dependency overridden to use temp dir

### Code Quality

```bash
# Format & lint
uv run ruff check .          # Check for issues
uv run ruff check --fix .    # Auto-fix
uv run black .               # Format code
uv run isort .               # Sort imports

# Pre-commit runs these automatically
pre-commit run --all-files
```

**Conventions** (enforced by ruff + black):
- Line length: 100 characters
- Double quotes for strings
- Import order: isort with black profile

## Important Notes

### FileHandler Validation

FileHandler validates all inputs before file operations:
1. Paths must be relative (not absolute) — raises `CustomError(400)` if violated
2. Paths must exist within `BASE_DIR` — raises `CustomError(404)` if missing
3. File operations check file/dir type — raises `CustomError(404)` if wrong type
4. Write operations prevent overwriting existing files — raises `CustomError(400)`

### Frontmatter Parsing

- Frontmatter must be enclosed by `---` on separate lines at the file start.
- Content after the closing `---` is treated as text content.
- If no frontmatter exists, `get_frontmatter()` returns `{}`.
- `yaml.safe_load()` is used (no arbitrary Python execution).

### Base Directory

The `BASE_DIR` is determined by the `BASE_DIR` environment variable or defaults to the app directory. In Docker, it's set to `/app/data` and mounted from `./scratch/vault`.

## CI/CD

GitHub Actions workflow (`.github/workflows/build.yaml`):
1. **version_check** — Ensures no duplicate versions in Docker registry (uses `utils/check_version.py`)
2. **test** — Runs pytest with coverage
3. **lint** — Runs ruff, black, isort checks
4. **build** — Builds and pushes multi-arch Docker image (amd64, arm64) to ghcr.io on main branch push

## File Structure

```
app/
├── main.py              # FastAPI app
├── router.py            # HTTP endpoints
├── file_handler.py      # Core file operations
├── exception.py         # CustomError class
├── env.py               # Environment config
└── test/
    ├── conftest.py      # pytest fixtures
    ├── test_main.py     # Basic tests
    └── v1/              # Endpoint tests
```
