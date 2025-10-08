#!/usr/bin/env bash
set -euo pipefail

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn is required for the demo. Install extras with 'pip install \".[dev]\"'." >&2
  exit 1
fi

export INVENTORY_DATA_PATH=${INVENTORY_DATA_PATH:-scripts/fixtures/inventory.json}
export PRICING_DATA_PATH=${PRICING_DATA_PATH:-scripts/fixtures/pricing.json}

trap '[[ -n "${INV_PID:-}" ]] && kill ${INV_PID} >/dev/null 2>&1 || true;
      [[ -n "${PR_PID:-}" ]] && kill ${PR_PID} >/dev/null 2>&1 || true;
      [[ -n "${GW_PID:-}" ]] && kill ${GW_PID} >/dev/null 2>&1 || true' EXIT

uvicorn apps.mcp_inventory.app.main:app --port 8100 --log-level warning &
INV_PID=$!
uvicorn apps.mcp_pricing.app.main:app --port 8200 --log-level warning &
PR_PID=$!

sleep 2
uvicorn apps.gateway.main:app --port 8080 --log-level warning &
GW_PID=$!

sleep 3
python -m clients.mock-agent || true

echo "Stopping demo services..."
