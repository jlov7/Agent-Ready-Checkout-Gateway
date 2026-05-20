from __future__ import annotations

import asyncio
from typing import Any


class ExampleAdapter:
    """A stub PSP adapter illustrating the interface required by the gateway.

    This adapter performs no network IO and should be used for tests, demos,
    or as a template when integrating additional payment providers.
    """

    async def create_payment_intent(
        self, *, amount_cents: int, currency: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        await asyncio.sleep(0)
        return {
            "id": "example_intent",
            "client_secret": "example_client_secret",
            "status": "requires_confirmation",
            "amount": amount_cents,
            "currency": currency,
            "metadata": metadata,
        }

    async def confirm_payment(self, *, intent_id: str, payment_method_token: str) -> dict[str, Any]:
        await asyncio.sleep(0)
        return {
            "id": intent_id,
            "status": "succeeded",
            "charges": {"data": [{"id": f"example_charge_{payment_method_token}"}]},
        }

    async def capture_payment(self, *, intent_id: str) -> dict[str, Any]:
        await asyncio.sleep(0)
        return {"id": intent_id, "status": "succeeded"}
