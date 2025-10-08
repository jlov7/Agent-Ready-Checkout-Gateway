from __future__ import annotations

import asyncio
from typing import Any, Dict

try:
    import stripe
except ImportError:  # pragma: no cover - optional dependency
    stripe = None  # type: ignore


class StripeAdapter:
    """Stripe test-mode adapter using tokenized payments."""

    def __init__(self, api_key: str):
        if stripe is None:
            raise RuntimeError("stripe package is required. Install stripe to enable payment processing.")
        stripe.api_key = api_key
        stripe.api_version = "2022-11-15"

    async def create_payment_intent(
        self, *, amount_cents: int, currency: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        payload = dict(amount=amount_cents, currency=currency, payment_method_types=["card"], metadata=metadata)
        intent = await asyncio.to_thread(stripe.PaymentIntent.create, **payload)
        return intent

    async def confirm_payment(
        self, *, intent_id: str, payment_method_token: str
    ) -> Dict[str, Any]:
        intent = await asyncio.to_thread(
            stripe.PaymentIntent.confirm, intent_id, payment_method=payment_method_token
        )
        return intent

    async def capture_payment(self, *, intent_id: str) -> Dict[str, Any]:
        intent = await asyncio.to_thread(stripe.PaymentIntent.capture, intent_id)
        return intent

    async def issue_refund(self, *, intent_id: str, reason: str) -> Dict[str, Any]:
        refund = await asyncio.to_thread(
            stripe.Refund.create, payment_intent=intent_id, reason=reason
        )
        return refund
