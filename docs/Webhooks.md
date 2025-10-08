# Stripe Webhook Verification

Use Stripe's official SDK to verify webhook payloads before processing events. Failing closed prevents replay or spoofing attacks.

```python
import stripe
from fastapi import HTTPException, Request

stripe.api_key = "${STRIPE_API_KEY}"
STRIPE_WEBHOOK_SECRET = "${STRIPE_WEBHOOK_SECRET}"

async def handle_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="missing signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError as exc:  # fail closed
        raise HTTPException(status_code=400, detail="invalid webhook signature") from exc

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        # TODO: mark order as settled using payment_intent["id"]

    return {"received": True}
```

Enforce idempotency for webhook handlers by storing `event["id"]` and ignoring duplicates.
