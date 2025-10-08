from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, String

from .database import Base


class ConsentLedgerEntry(Base):
    __tablename__ = "consent_ledger"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    intent_id = Column(String(36), nullable=False, index=True)
    transcript_hash = Column(String(64), nullable=False, index=True)
    previous_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=False)
    payload = Column(JSON, nullable=False)
    customer_ip = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def to_dict(entry: ConsentLedgerEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "intent_id": entry.intent_id,
        "transcript_hash": entry.transcript_hash,
        "previous_hash": entry.previous_hash,
        "entry_hash": entry.entry_hash,
        "payload": entry.payload,
        "customer_ip": entry.customer_ip,
        "user_agent": entry.user_agent,
        "created_at": entry.created_at.isoformat(),
    }
