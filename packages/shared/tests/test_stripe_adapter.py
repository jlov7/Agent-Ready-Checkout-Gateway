from __future__ import annotations

import asyncio

import pytest

from packages.shared.shared.psp.stripe_adapter import StripeAdapter

stripe = pytest.importorskip("stripe")


@pytest.mark.asyncio
async def test_create_payment_intent_invokes_stripe(monkeypatch):
    calls = {}

    def fake_create(**kwargs):
        calls.update(kwargs)
        return {"id": "pi_fake", "client_secret": "cs_fake"}

    monkeypatch.setattr(stripe.PaymentIntent, "create", fake_create)

    adapter = StripeAdapter("sk_test")
    result = await adapter.create_payment_intent(
        amount_cents=1234,
        currency="usd",
        metadata={"foo": "bar"},
    )
    assert result["id"] == "pi_fake"
    assert calls["amount"] == 1234
    assert calls["currency"] == "usd"
    assert calls["metadata"] == {"foo": "bar"}


@pytest.mark.asyncio
async def test_confirm_payment_uses_token(monkeypatch):
    captured = {}

    def fake_confirm(intent_id, payment_method):
        captured["intent_id"] = intent_id
        captured["payment_method"] = payment_method
        return {"id": intent_id, "status": "succeeded", "charges": {"data": []}}

    monkeypatch.setattr(stripe.PaymentIntent, "confirm", fake_confirm)

    adapter = StripeAdapter("sk_test")
    result = await adapter.confirm_payment(intent_id="pi_fake", payment_method_token="pm_card")
    assert result["status"] == "succeeded"
    assert captured == {"intent_id": "pi_fake", "payment_method": "pm_card"}
