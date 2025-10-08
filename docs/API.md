# API Contract

This document provides an overview of the ACP Agent-Ready Checkout Gateway API. The canonical contract is published as `apps/gateway/openapi.json` and served by the FastAPI application.

OpenAPI explorer endpoints:

- JSON: `/openapi.json`
- Swagger UI: `/docs`
- Redoc: `/redoc`

## Base URL

```
https://{gateway-host}/api/v1
```

All endpoints require HTTPS with HSTS and expect JSON payloads encoded as UTF-8.

## Endpoints

### POST `/intents`

Initiate an ACP order intent. Validates schema, domain allow-list, and rate-limit policy. Returns a nonce, intent identifier, and required confirmation steps.

### POST `/confirm`

Record explicit human consent. Appends to the consent ledger with timestamp, IP, user-agent, and hash linkage. Enforces nonce expiry.

Headers:

- `Idempotency-Key` (optional) — identical payloads replay cached responses; mismatched payloads return HTTP 409.

### POST `/authorize`

Performs payment authorization through the configured PSP adapter (Stripe test-mode by default). Requires a valid consent transcript hash. Returns masked payment reference alongside the policy hook outcome.

Headers:

- `Idempotency-Key` (optional) — identical payloads replay cached responses; mismatched payloads return HTTP 409.

### POST `/fulfil`

Marks an order as fulfilled, issues signed receipts (PNG + PDF), and publishes telemetry events. Requires the authorization token from the previous step.

## Error model

Errors follow the structure:

```json
{
  "error": {
    "code": "string",
    "message": "human readable",
    "details": {}
  },
  "trace_id": "uuid"
}
```

Authorization responses extend the schema with:

```json
{
  "policy_decision": "ALLOW | DENY | REVIEW",
  "policy_reasons": ["human readable justification"]
}
```

The default policy hook lives in `apps/gateway/app/policies/policy_hook.py` and can be replaced with bespoke trust-and-safety logic.

## Security headers

- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `Content-Security-Policy: default-src 'none'`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-Ratelimit-Limit` / `X-Ratelimit-Remaining`

## Webhooks

Stripe webhooks are verified via HMAC SHA-256 using `HMAC_WEBHOOK_SECRET`. Payloads are recorded in the consent ledger as audit entries. See `docs/Webhooks.md` for a fail-closed verification example and idempotency guidance.
