from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from packages.shared.shared.utils.crypto import compute_hmac

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_gateway.db")
os.environ.setdefault("STRIPE_API_KEY", "sk_test_stub")
os.environ.setdefault("HMAC_WEBHOOK_SECRET", "secret123")
os.environ.setdefault("ALLOWED_AGENT_DOMAINS", "agents.example.com")


class FakeStripeAdapter:
    def __init__(self):
        self.created: Dict[str, Any] = {}
        self.confirmed: Dict[str, Any] = {}

    async def create_payment_intent(
        self, *, amount_cents: int, currency: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.created = {
            "id": "pi_test_123",
            "client_secret": "secret_test",
            "amount": amount_cents,
            "currency": currency,
            "metadata": metadata,
        }
        return self.created

    async def confirm_payment(self, *, intent_id: str, payment_method_token: str) -> Dict[str, Any]:
        self.confirmed = {
            "id": intent_id,
            "status": "succeeded",
            "charges": {"data": [{"id": "ch_test_123"}]},
        }
        return self.confirmed

    async def capture_payment(self, *, intent_id: str) -> Dict[str, Any]:
        return {"id": intent_id, "status": "succeeded"}


@pytest.fixture
def client(monkeypatch):
    from apps.gateway.main import create_app
    from apps.gateway.app.core.deps import get_stripe_adapter

    db_path = Path("test_gateway.db")
    if db_path.exists():
        db_path.unlink()

    app = create_app()
    fake_adapter = FakeStripeAdapter()

    def override_adapter():
        return fake_adapter

    app.dependency_overrides[get_stripe_adapter] = override_adapter

    with TestClient(app) as client:
        yield client


def _sign_transcript(transcript: Dict[str, Any], secret: str) -> None:
    import json
    from copy import deepcopy

    payload = deepcopy(transcript)
    payload["signature"]["value"] = ""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    signature = compute_hmac(secret, f"{transcript['signature']['nonce']}:{canonical}")
    transcript["signature"]["value"] = signature


def test_order_happy_path(client: TestClient):
    receipts_dir = Path("receipts")
    if receipts_dir.exists():
        for file in receipts_dir.iterdir():
            file.unlink()

    create_resp = client.post(
        "/api/v1/intents",
        json={
            "agent_id": "https://agents.example.com/agent/123",
            "customer_id": "https://customers.example.com/user/456",
            "cart": {"items": [{"sku": "SKU123", "quantity": 1}]},
            "max_total": 42.50,
            "currency": "usd",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    data = create_resp.json()
    intent_id = data["intent_id"]
    nonce = data["nonce"]

    transcript = {
        "agent_id": "https://agents.example.com/agent/123",
        "customer_id": "https://customers.example.com/user/456",
        "intent": {
            "id": intent_id,
            "expires_at": "2099-01-01T00:00:00+00:00",
            "actions": [],
        },
        "confirmation": {
            "method": "human",
            "timestamp": "2099-01-01T00:00:01+00:00",
            "channel": "web",
        },
        "signature": {
            "alg": "HS256",
            "nonce": nonce,
            "value": "",
        },
        "version": "1.0",
    }
    _sign_transcript(transcript, os.environ["HMAC_WEBHOOK_SECRET"])

    confirm_resp = client.post(
        "/api/v1/confirm",
        json={
            "intent_id": intent_id,
            "transcript": transcript,
            "customer_ip": "203.0.113.10",
            "user_agent": "pytest",
        },
    )
    assert confirm_resp.status_code == 200, confirm_resp.text
    confirm_data = confirm_resp.json()

    authorize_resp = client.post(
        "/api/v1/authorize",
        json={
            "intent_id": intent_id,
            "transcript_hash": confirm_data["transcript_hash"],
            "payment_method_token": "pm_card_visa",
        },
    )
    assert authorize_resp.status_code == 200, authorize_resp.text

    fulfil_resp = client.post(
        "/api/v1/fulfil",
        json={
            "intent_id": intent_id,
            "authorization_id": authorize_resp.json()["authorization_id"],
            "fulfillment_reference": "SHIP123",
        },
    )
    assert fulfil_resp.status_code == 200, fulfil_resp.text
    fulfil_data = fulfil_resp.json()
    assert Path(fulfil_data["receipt_png_path"]).exists()
    assert Path(fulfil_data["receipt_pdf_path"]).exists()


def _create_intent(client: TestClient) -> Dict[str, Any]:
    resp = client.post(
        "/api/v1/intents",
        json={
            "agent_id": "https://agents.example.com/agent/123",
            "customer_id": "https://customers.example.com/user/456",
            "cart": {"items": [{"sku": "SKU123", "quantity": 1}]},
            "max_total": 42.50,
            "currency": "usd",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_intent_blocks_unlisted_domain(client: TestClient):
    resp = client.post(
        "/api/v1/intents",
        json={
            "agent_id": "https://evil.example.net/bot",
            "customer_id": "https://customers.example.com/user/456",
            "cart": {"items": [{"sku": "SKU123", "quantity": 1}]},
            "max_total": 42.50,
            "currency": "usd",
        },
    )
    assert resp.status_code == 403


def test_confirm_rejects_nonce_mismatch(client: TestClient):
    data = _create_intent(client)
    transcript = {
        "agent_id": "https://agents.example.com/agent/123",
        "customer_id": "https://customers.example.com/user/456",
        "intent": {
            "id": data["intent_id"],
            "expires_at": "2099-01-01T00:00:00+00:00",
            "actions": [],
        },
        "confirmation": {
            "method": "human",
            "timestamp": "2099-01-01T00:00:01+00:00",
            "channel": "web",
        },
        "signature": {
            "alg": "HS256",
            "nonce": "wrong-nonce",
            "value": "",
        },
        "version": "1.0",
    }
    _sign_transcript(transcript, os.environ["HMAC_WEBHOOK_SECRET"])
    resp = client.post(
        "/api/v1/confirm",
        json={"intent_id": data["intent_id"], "transcript": transcript},
    )
    assert resp.status_code == 400


def test_confirm_detects_nonce_replay(client: TestClient):
    data = _create_intent(client)
    transcript = {
        "agent_id": "https://agents.example.com/agent/123",
        "customer_id": "https://customers.example.com/user/456",
        "intent": {
            "id": data["intent_id"],
            "expires_at": "2099-01-01T00:00:00+00:00",
            "actions": [],
        },
        "confirmation": {
            "method": "human",
            "timestamp": "2099-01-01T00:00:01+00:00",
            "channel": "web",
        },
        "signature": {
            "alg": "HS256",
            "nonce": data["nonce"],
            "value": "",
        },
        "version": "1.0",
    }
    _sign_transcript(transcript, os.environ["HMAC_WEBHOOK_SECRET"])

    first = client.post(
        "/api/v1/confirm",
        json={"intent_id": data["intent_id"], "transcript": transcript},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/confirm",
        json={"intent_id": data["intent_id"], "transcript": transcript},
    )
    assert second.status_code == 409


def test_authorize_requires_confirmation(client: TestClient):
    data = _create_intent(client)
    resp = client.post(
        "/api/v1/authorize",
        json={
            "intent_id": data["intent_id"],
            "transcript_hash": "not-real",
            "payment_method_token": "pm_card_visa",
        },
    )
    assert resp.status_code == 409
