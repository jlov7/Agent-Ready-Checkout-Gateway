# ACP Integration Notes

## Transcript schema

The gateway expects ACP transcripts structured as:

```json
{
  "agent_id": "uri",
  "customer_id": "uri",
  "intent": {
    "id": "uuid",
    "expires_at": "iso-8601",
    "actions": [
      {
        "type": "inventory.lookup",
        "tool_call_id": "uuid",
        "inputs": {},
        "outputs": [
          { "sku": "string", "quantity": 1 }
        ]
      }
    ]
  },
  "confirmation": {
    "method": "human",
    "timestamp": "iso-8601",
    "channel": "web"
  },
  "signature": {
    "alg": "EdDSA",
    "nonce": "random",
    "value": "base64"
  }
}
```

Validation occurs via `pydantic` models located in `packages/shared/shared/schemas/acp.py`. The schema enforces:

- ISO-8601 timestamps with timezone offsets
- Non-expired `intent.expires_at`
- Domain allow-list on `agent_id`
- Unique `tool_call_id` values to prevent replay

## Hash chaining

Each consent entry is stored with:

- `transcript_hash` (SHA-256 of the normalized JSON)
- `previous_hash` (SHA-256 of the prior entry)
- `entry_hash` (SHA-256 of `transcript_hash + previous_hash + metadata`)

Ledger integrity can be verified by re-computing the chain in order of `created_at`.

## Nonce & replay protection

- Nonce must be 128 bits of entropy, base64url encoded.
- TTL enforced via `NONCE_TTL_SECONDS` env variable.
- Nonces are persisted in Redis-compatible cache (see `NonceService`); default uses in-memory expiring store for development.
- Clients should combine nonces with `Idempotency-Key` headers on `/confirm` and `/authorize` so accidental retries return cached responses instead of tripping replay detections.

## Signatures

The gateway supports HMAC-based signatures (`Alg=HS256`). Extend `packages/shared/shared/security/signatures.py` to add EdDSA or other algorithms as needed. Signatures include the nonce, canonical transcript JSON, and timestamp.

## MCP tool metadata

- Inventory manifest: `GET http://localhost:8100/mcp/manifest`
- Pricing manifest: `GET http://localhost:8200/mcp/manifest`
- Demo agent: `python -m clients.mock-agent`

Tools exposed via MCP align with the transcript `intent.actions[].type` identifiers (`inventory.lookup`, `pricing.quote`).
