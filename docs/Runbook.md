# Operations Runbook

## Service overview

- FastAPI app served via Uvicorn / Gunicorn
- Postgres 15 backing consent ledger
- Langfuse collector for agent/tool telemetry
- OTEL collector exporting traces to Langfuse (OTLP)

## Health checks

- `/health/live` – process health
- `/health/ready` – DB connectivity, Stripe connectivity, certificate presence

## On-call checklist

1. Check Langfuse dashboard for recent errors and latency spikes.
2. Inspect structured logs filtered by `trace_id` for failing intents.
3. Validate ledger integrity using `python -m apps.gateway.scripts.verify_ledger`.
4. Confirm receipt signing keys are valid (`openssl x509 -in cert.pem -noout -text`).

## Common incidents

### Stripe authorization failures

- Inspect Stripe dashboard (test mode) for declines.
- Verify `STRIPE_API_KEY` and `STRIPE_WEBHOOK_SECRET`.
- Recreate a tokenized payment via `scripts/demo_payment.py`.

### Replay attack detected

- Review consent ledger for duplicated nonce.
- Verify agent domain allow-list.
- Rotate shared secrets if signature mismatch.

### Receipt signing errors

- Ensure C2PA CLI dependencies installed.
- Certificates must allow signing and not be expired.
- Temporary mitigation: fallback to unsigned receipt, flag order for manual review.

## Disaster recovery

- Postgres backups: nightly snapshot, point-in-time restore.
- Ledger hash chain validated on restore before accepting new traffic.
- Stripe tokens are ephemeral; re-initiate payment if window elapsed.

## Contact

- Security incident: security@yourcompany.example
- On-call rotation: `#oncall-agent-gateway` Slack channel.
