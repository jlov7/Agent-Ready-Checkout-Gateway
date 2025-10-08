# Agent-Ready Checkout Gateway

Turn any shop into agent-ready checkout: consented orders from AI agents, with audit trails and C2PA-stamped receipts. This is an **alpha** reference implementation—pattern demo, not a drop-in PCI replacement.

## Features

- ACP-compliant FastAPI gateway with `/intents`, `/confirm`, `/authorize`, `/fulfil`
- Stripe test-mode adapter plus a portable example PSP stub
- Append-only consent ledger backed by Postgres with hash chaining and idempotency keys
- Policy hook (allow/deny/review) invoked on authorization, with reasons in responses
- C2PA-ready receipt pipeline with graceful fallbacks when optional deps are absent
- OpenTelemetry + Langfuse observability, structured JSON logs, and trace correlation
- Mock MCP inventory/pricing servers, LangGraph demo agent, and Postman collection

![Gateway demo flow](docs/media/demo-flow.gif)

## Quickstart

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
make install
docker compose up -d --build
alembic upgrade head
uvicorn apps.gateway.main:app --reload
```

Navigate to:

- OpenAPI JSON: `http://localhost:8080/openapi.json`
- Swagger UI: `http://localhost:8080/docs`
- Redoc UI: `http://localhost:8080/redoc`

**Optional extras:** install `pillow`, `reportlab`, `c2pa-python`, `stripe`, and `slowapi` to enable signed receipts, PSP calls, and rate limiting. Without them, the gateway emits informative warnings.

### Seed sample data

```bash
./scripts/seed_demo.sh
```

### Run tests, lint, and security scan

```bash
make test
make lint
bandit -r apps packages clients
```

### Demo the full flow (inventory → pricing → gateway → mock agent)

```bash
make demo
```

The helper script launches the MCP mocks, gateway, and CLI agent, then tears them down automatically.

### Curl snippets

```bash
BASE=http://localhost:8080

# 1. Intent
curl -X POST "$BASE/api/v1/intents" \
  -H 'Content-Type: application/json' \
  -d '{"agent_id":"https://agents.example.com/agent/123","customer_id":"https://customers.example.com/user/456","cart":{"items":[{"sku":"SKU123","quantity":1}]},"max_total":42.5,"currency":"usd"}'

# 2. Confirm (include Idempotency-Key)
curl -X POST "$BASE/api/v1/confirm" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: confirm-123' \
  -d '{"intent_id":"<intent_uuid>","transcript":{...}}'

# 3. Authorize (policy hook runs here)
curl -X POST "$BASE/api/v1/authorize" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: authorize-123' \
  -d '{"intent_id":"<intent_uuid>","transcript_hash":"<hash>","payment_method_token":"pm_card_visa"}'

# 4. Fulfil
curl -X POST "$BASE/api/v1/fulfil" \
  -H 'Content-Type: application/json' \
  -d '{"intent_id":"<intent_uuid>","authorization_id":"<auth_uuid>","fulfillment_reference":"SHIP123"}'
```

Import `docs/postman/agent-ready.postman_collection.json` into Postman/Insomnia for ready-made requests.

## ACP transcript example

```jsonc
{
  "agent_id": "https://agents.example.com/agent/123",
  "customer_id": "https://customers.example.com/user/456",
  "intent": {
    "id": "4b5c6d7e-1234-5678-9abc-0123456789ab",
    "expires_at": "2024-03-08T21:15:00Z",
    "actions": [
      {
        "type": "inventory.lookup",
        "tool_call_id": "0f1e2d3c-4567-8901-2345-6789abcdef01",
        "inputs": {"sku": "SKU123"},
        "outputs": [{"sku": "SKU123", "quantity": 1}]
      }
    ]
  },
  "confirmation": {
    "method": "human",
    "timestamp": "2024-03-08T21:10:00Z",
    "channel": "web"
  },
  "signature": {
    "alg": "HS256",
    "nonce": "M3RjX19hY2...",
    "value": "1c5a6b3e..."
  },
  "version": "1.0"
}
```

See `docs/ACP.md` for schema validation notes and replay protection details.

## Policy hook & idempotency

- `apps/gateway/app/policies/policy_hook.py` returns `ALLOW`, `DENY`, or `REVIEW` with human-readable reasons. `/authorize` responses surface `policy_decision` and `policy_reasons`.
- `/confirm` and `/authorize` honour the `Idempotency-Key` header. Replays with different payloads are rejected; matching payloads replay cached responses.

## Webhooks

- Example Stripe signature verification: `docs/Webhooks.md`
- Always store `event.id` for idempotency and fail closed on signature mismatch.

## Observability quickstart

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export LANGFUSE_HOST=http://localhost:3000
export LANGFUSE_PUBLIC_KEY=public_dev
export LANGFUSE_SECRET_KEY=secret_dev
```

![Langfuse trace](docs/media/langfuse-trace.png)

## Repository layout

```
apps/gateway          FastAPI application implementing ACP endpoints
apps/mcp_inventory    Mock inventory MCP server (MCP manifest + tool)
apps/mcp_pricing      Mock pricing MCP server
clients/mock-agent    LangGraph demo agent that walks through an order
packages/shared       Shared DTOs, config, logging, ledger, security utilities
docs                  Architecture overview, API contracts, threat model, postman
scripts               Maintenance scripts (seed, run_demo, openapi exporter)
```

## Documentation

- `docs/API.md` – endpoint contract and headers
- `docs/ACP.md` – ACP schema and replay protection notes
- `docs/ThreatModel.md` – mitigations, residual risks, and summary bullets
- `docs/Runbook.md` – operational playbook
- `docs/Webhooks.md` – Stripe verification example

## Privacy

No personal data or PII is processed or stored by this demo. Inputs and outputs remain in-memory test payloads only.

## Status

Alpha (`v0.1.0`). Contributions welcome—see `CONTRIBUTING.md`.

---

Personal R&D project, unaffiliated with my employer. Built on personal time/equipment. No client or confidential information used. Provided “as is,” without warranties. Opinions are my own.
