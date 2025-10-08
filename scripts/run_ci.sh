#!/usr/bin/env bash
set -euo pipefail

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
DATABASE_URL=${DATABASE_URL:-sqlite+aiosqlite:///${PWD}/test.db} \
STRIPE_API_KEY=${STRIPE_API_KEY:-sk_test_placeholder} \
HMAC_WEBHOOK_SECRET=${HMAC_WEBHOOK_SECRET:-secret123} \
pytest -p pytest_cov

ruff check .
mypy .
bandit -r apps packages clients
