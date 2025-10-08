# Contributing

Thanks for helping build the Agent-Ready Checkout Gateway! This is a personal R&D project and contributions are welcome on a best-effort basis.

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
- Include a `Signed-off-by:` line (Developer Certificate of Origin) on every commit.

## Commit guidelines

- Conventional commits are recommended (`feat:`, `fix:`, `chore:`).
- Keep commits focused and well-described.
- Include references to related issues.

## Developer Certificate of Origin (DCO)

This project requires every contribution to be signed off in accordance with the [Developer Certificate of Origin](https://developercertificate.org/). Each commit message must include the following line (using your real name and email):

```
Signed-off-by: Your Name <you@example.com>
```

You can automate this with `git commit -s`.

## Code of Conduct

By participating, you agree to uphold the [Code of Conduct](CODE_OF_CONDUCT.md). Report issues to `conduct@yourcompany.example`.
