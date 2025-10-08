# Agent-Ready Checkout Gateway

Turn any shop into agent-ready checkout: consented orders from AI agents, with audit trails and C2PA-stamped receipts.

## Features

- ACP-compliant FastAPI gateway with `/intents`, `/confirm`, `/authorize`, `/fulfil` endpoints
- Stripe test-mode payment adapter with clean abstraction for future PSPs
- Append-only consent ledger backed by Postgres with hash chaining
- OpenTelemetry + Langfuse observability, structured JSON logs, and trace correlation
- Mock MCP inventory/pricing servers and a LangGraph-based demo agent
- C2PA-signed PNG/PDF receipt generation with embedded provenance metadata

## Quickstart

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
make install
docker compose up -d --build
alembic upgrade head
uvicorn apps.gateway.main:app --reload
```

> The project targets Python 3.11+. `make install` installs all dev dependencies; alternatively run `pip install ".[dev]"`.

**Optional packages:** install `pillow`, `reportlab`, `c2pa-python`, and `stripe` to enable signed receipt generation and live payment flows. In development, the gateway falls back to informative runtime errors if these libraries are missing.

### Seed sample data

```bash
./scripts/seed_demo.sh
```

### Run tests & linters

```bash
make test
make lint
bandit -r apps packages clients   # security scan
```

## Repository layout

- gateway/orders/intent → orchestrates Stripe PaymentIntent creation and nonce issuance
- gateway/orders/confirm → appends signed consent transcripts to Postgres hash-chain ledger
- gateway/orders/authorize → confirms tokenised card payments with Stripe (test mode)
- gateway/orders/fulfil → produces signed PNG/PDF receipts enriched with ACP transcript metadata

### MCP mocks and demo agent

- Inventory MCP server: `uvicorn apps.mcp_inventory.app.main:app --port 8100`
- Pricing MCP server: `uvicorn apps.mcp_pricing.app.main:app --port 8200`
- Demo LangGraph agent: `python -m clients.mock-agent`

The agent fetches inventory/pricing via MCP, collects human confirmation in the CLI, and walks the gateway through the `/intents → /confirm → /authorize → /fulfil` flow.

### Database migrations

Apply schema changes with Alembic:

```bash
alembic upgrade head
```

See `alembic/` for migration scripts. The gateway auto-creates tables in development, but production deployments should run migrations explicitly.
apps/gateway          FastAPI application implementing ACP endpoints
apps/mcp_inventory    Mock inventory MCP server
apps/mcp_pricing      Mock pricing MCP server
clients/mock-agent    LangGraph demo agent that walks through an order
packages/shared       Shared DTOs, config, logging, ledger, security utilities
docs                  Architecture overview, API contracts, threat model
scripts               Maintenance and demo scripts (seed data, etc.)
```

## Documentation

- `docs/API.md` – OpenAPI contract and endpoint conventions
- `docs/ThreatModel.md` – Security assumptions, mitigations, and controls
- `docs/ACP.md` – ACP transcript structure and schema validation notes
- `docs/Runbook.md` – Operational playbook for on-call teams

## Status

The repository is pre-release (`v0.1.0`). Contributions are welcome—see `CONTRIBUTING.md`.
