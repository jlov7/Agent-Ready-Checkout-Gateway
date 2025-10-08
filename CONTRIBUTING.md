# Contributing

Thanks for helping build the Agent-Ready Checkout Gateway! This guide describes how to get started.

## Getting started

1. Install Python 3.11+ and [uv](https://github.com/astral-sh/uv) or poetry.
2. Create a virtualenv and install dependencies:
   ```bash
   uv sync --dev
   ```
3. Copy `.env.example` to `.env` and update values.
4. Start dependencies: `docker compose up -d`.

## Development workflow

- `ruff check .` – lint
- `mypy .` – type checks
- `pytest` – run unit + API tests (requires Postgres)
- `pytest --cov` – coverage; target 90% line coverage

Before opening a PR:

- Ensure CI passes locally (`scripts/run_ci.sh` mirrors GH Actions).
- Update documentation (`docs/`) and `CHANGELOG.md`.
- Add or update tests for new behaviour.

## Commit guidelines

- Conventional commits are recommended (`feat:`, `fix:`, `chore:`).
- Keep commits focused and well-described.
- Include references to related issues.

## Code of Conduct

By participating, you agree to uphold the [Code of Conduct](CODE_OF_CONDUCT.md). Report issues to `conduct@yourcompany.example`.
