from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from .acp import ACPTranscript


class IntentCreateRequest(BaseModel):
    agent_id: str
    customer_id: str
    cart: dict[str, Any]
    max_total: float
    currency: str = "usd"


class IntentCreateResponse(BaseModel):
    intent_id: UUID
    nonce: str
    client_secret: str
    expires_at: datetime


class ConfirmRequest(BaseModel):
    intent_id: UUID
    transcript: ACPTranscript
    customer_ip: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)


class ConfirmResponse(BaseModel):
    confirmed_at: datetime
    ledger_entry_id: UUID
    transcript_hash: str


class AuthorizeRequest(BaseModel):
    intent_id: UUID
    transcript_hash: str
    payment_method_token: str


class AuthorizeResponse(BaseModel):
    authorization_id: UUID
    payment_reference: str
    amount_cents: int
    currency: str
    captured: bool = False
    policy_decision: str
    policy_reasons: list[str]


class FulfilRequest(BaseModel):
    intent_id: UUID
    authorization_id: UUID
    fulfillment_reference: str


class FulfilResponse(BaseModel):
    fulfilment_id: UUID
    receipt_png_path: str
    receipt_pdf_path: str
    transcript_hash: str
    issued_at: datetime
