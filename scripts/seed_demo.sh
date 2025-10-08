#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

INVENTORY_FILE="${ROOT_DIR}/scripts/fixtures/inventory.json"
PRICING_FILE="${ROOT_DIR}/scripts/fixtures/pricing.json"

cat > "${INVENTORY_FILE}" <<'JSON'
[
  {
    "sku": "SKU123",
    "name": "Agent Starter Kit",
    "quantity": 25,
    "warehouse": "FULFILLMENT-1"
  },
  {
    "sku": "SKU456",
    "name": "Consent Ledger Notebook",
    "quantity": 40,
    "warehouse": "FULFILLMENT-2"
  }
]
JSON

cat > "${PRICING_FILE}" <<'JSON'
{
  "SKU123": {
    "currency": "USD",
    "unit_price": 4250,
    "description": "Agent Starter Kit"
  },
  "SKU456": {
    "currency": "USD",
    "unit_price": 1500,
    "description": "Consent Ledger Notebook"
  }
}
JSON

echo "Seeded demo data:"
echo "  Inventory -> ${INVENTORY_FILE}"
echo "  Pricing   -> ${PRICING_FILE}"
