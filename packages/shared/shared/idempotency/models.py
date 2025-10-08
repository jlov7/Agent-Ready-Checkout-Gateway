from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, UniqueConstraint

from packages.shared.shared.ledger.database import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("key", "endpoint", name="uq_idempotency_endpoint"),
    )

    key = Column(String(128), primary_key=True)
    endpoint = Column(String(64), primary_key=True)
    payload_hash = Column(String(64), nullable=False)
    response_body = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
