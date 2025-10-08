# Changelog

All notable changes to this project will be documented in this file.

## v0.1.0 - Unreleased

- Scaffolded ACP Agent-Ready Checkout Gateway monorepo structure
- Added FastAPI gateway, consent ledger, Stripe adapter, and receipt service
- Implemented mock MCP inventory and pricing servers plus demo agent
- Wired OpenTelemetry, Langfuse telemetry, and structured logging
- Documented API contracts, threat model, and operational playbook
- Added CI pipeline, docker-compose stack, and developer tooling
- Persisted order intents + idempotency records in Postgres with Alembic migrations and expanded API tests
- Added policy hook, PSP stub adapter, Postman collection, and documentation for idempotency/webhook hygiene
- Added optional fallbacks for optional dependencies, observability quickstart, make demo, and security tooling
