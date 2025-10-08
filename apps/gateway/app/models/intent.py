from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String

from packages.shared.shared.ledger.database import Base


class OrderIntent(Base):
    __tablename__ = "order_intents"

    id = Column(String(36), primary_key=True)
    nonce = Column(String(128), nullable=False)
    stripe_intent_id = Column(String(255), nullable=False)
    client_secret = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(16), nullable=False)
    items = Column(JSON, nullable=False)
    agent_id = Column(String(255), nullable=False)
    customer_id = Column(String(255), nullable=False)
    transcript_hash = Column(String(64), nullable=True)
    authorization_id = Column(String(36), nullable=True)
    payment_reference = Column(String(128), nullable=True)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)
    receipts = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nonce": self.nonce,
            "stripe_intent_id": self.stripe_intent_id,
            "client_secret": self.client_secret,
            "expires_at": self.expires_at.isoformat(),
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "items": self.items,
            "agent_id": self.agent_id,
            "customer_id": self.customer_id,
            "transcript_hash": self.transcript_hash,
            "authorization_id": self.authorization_id,
            "payment_reference": self.payment_reference,
            "fulfilled_at": self.fulfilled_at.isoformat() if self.fulfilled_at else None,
            "receipts": self.receipts or {},
        }
