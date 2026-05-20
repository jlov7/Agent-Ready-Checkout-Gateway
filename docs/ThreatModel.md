# Threat Model

**Summary:**
- Consent drift: explicit `/confirm` with signed transcripts and policy hook review paths
- Replay attempts: nonce + TTL + idempotency ledger
- Tool-call loops: MCP tooling limited to deterministic mocks with rate limiting
- Provenance loss: receipts include detached manifests bound to the ledger hash chain
- Webhook spoofing: Stripe signature verification sample (fail closed)

## Scope

- FastAPI gateway (`apps/gateway`)
- Postgres-backed consent ledger
- Stripe test-mode adapter
- MCP mock servers (inventory and pricing)
- Receipt rendering and detached provenance manifest pipeline

## Assets

- Customer consent transcripts
- Payment authorization tokens
- Receipts (PNG/PDF) and detached provenance manifests
- Stripe API credentials
- Langfuse telemetry data

## Actors

- Legitimate MCP-capable agents invoking the gateway
- Human customers providing consent
- Malicious actors attempting replay, tampering, or fraud
- Insider threats with privileged access

## Trust boundaries

- External agents ↔ Gateway (HTTPS + signature validation)
- Gateway ↔ Stripe (Stripe SDK over TLS)
- Gateway ↔ Postgres (`DATABASE_URL`)
- Gateway ↔ Receipt signer (local process, sealed credentials)
- Gateway ↔ Langfuse/OTel (internal network)

## Threats & Mitigations

| Threat | Description | Mitigations |
| --- | --- | --- |
| Replay attacks | Reusing prior ACP intents | Nonce with TTL, hash-chain ledger, per-intent HMAC |
| Consent drift | Missing explicit human confirmation | `/confirm` enforces signed transcript step |
| Payment fraud | Unauthorized card usage | Stripe tokenized flow, idempotency keys, telemetry alerts |
| Data tampering | Ledger edits | Append-only hash chain, DB role with INSERT-only migration |
| DoS / brute force | Excess intent creation | `slowapi` rate limiter, domain allow-list, IP throttling |
| Receipt forgery | Missing provenance | Receipt manifests with SHA-256 digests and ledger hash linkage |
| Secret leakage | Misconfigured env | `.env.example`, secret scanning, `SECURITY.md` guidance |

## Residual risks

- Stripe test-mode does not simulate 3DS flows.
- MCP server mocks do not implement full auth; do not expose publicly.
- Embedded C2PA signing is not implemented in this alpha; production deployments should add a signer backed by protected keys.

## References

- ACP specification (v1.0)
- Stripe Payment Intents API
- C2PA Technical Specification
