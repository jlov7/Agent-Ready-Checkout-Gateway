# API Contract

This document provides an overview of the ACP Agent-Ready Checkout Gateway API. The canonical contract is published as `apps/gateway/openapi.json` and served by the FastAPI application.

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

### POST `/authorize`

Performs payment authorization through the configured PSP adapter (Stripe test-mode by default). Requires a valid consent transcript hash. Returns masked payment reference.

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

## Security headers

- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `Content-Security-Policy: default-src 'none'`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-Ratelimit-Limit` / `X-Ratelimit-Remaining`

## Webhooks

Stripe webhooks are verified via HMAC SHA-256 using `HMAC_WEBHOOK_SECRET`. Payloads are recorded in the consent ledger as audit entries.
