#!/usr/bin/env bash
set -euo pipefail

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
DATABASE_URL=${DATABASE_URL:-sqlite+aiosqlite:///./test_gateway.db} \
STRIPE_API_KEY=${STRIPE_API_KEY:-sk_test_placeholder} \
HMAC_WEBHOOK_SECRET=${HMAC_WEBHOOK_SECRET:-secret123} \
ALLOWED_AGENT_DOMAINS=${ALLOWED_AGENT_DOMAINS:-agents.example.com} \
uv run --python 3.11 --extra dev pytest -p pytest_cov

uv run --python 3.11 --extra dev ruff check .
uv run --python 3.11 --extra dev mypy .
uv run --python 3.11 --extra dev bandit -r apps packages clients -x '*/tests/*'
