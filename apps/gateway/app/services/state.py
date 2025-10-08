from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models.intent import OrderIntent


@dataclass
class IntentState:
    intent_id: UUID
    nonce: str
    stripe_intent_id: str
    client_secret: str
    expires_at: datetime
    amount_cents: int
    currency: str
    items: List[Dict[str, Any]]
    agent_id: str
    customer_id: str
    transcript_hash: Optional[str] = None
    authorization_id: Optional[UUID] = None
    payment_reference: Optional[str] = None
    fulfilled_at: Optional[datetime] = None
    receipts: Dict[str, str] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


class IntentStore:
    """Database-backed store for ACP order intents."""

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def create(
        self,
        *,
        amount_cents: int,
        currency: str,
        stripe_intent_id: str,
        client_secret: str,
        ttl_seconds: int,
        items: List[Dict[str, Any]],
        agent_id: str,
        customer_id: str,
    ) -> IntentState:
        intent_id = uuid4()
        nonce = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        record = OrderIntent(
            id=str(intent_id),
            nonce=nonce,
            stripe_intent_id=stripe_intent_id,
            client_secret=client_secret,
            expires_at=expires_at,
            amount_cents=amount_cents,
            currency=currency,
            items=items,
            agent_id=agent_id,
            customer_id=customer_id,
        )

        async with self._session_factory() as session:
            session.add(record)
            await session.commit()

        return self._to_state(record)

    async def get(self, intent_id: UUID) -> IntentState:
        async with self._session_factory() as session:
            record = await session.get(OrderIntent, str(intent_id))
            if record is None:
                raise KeyError("intent not found")

        state = self._to_state(record)
        if state.is_expired:
            raise ValueError("intent expired")
        return state

    async def set_transcript_hash(self, intent_id: UUID, transcript_hash: str) -> None:
        await self._update_fields(intent_id, {"transcript_hash": transcript_hash})

    async def set_authorization(
        self, intent_id: UUID, authorization_id: UUID, payment_reference: str
    ) -> None:
        await self._update_fields(
            intent_id,
            {
                "authorization_id": str(authorization_id),
                "payment_reference": payment_reference,
            },
        )

    async def set_fulfilled(self, intent_id: UUID, receipts: Dict[str, str]) -> None:
        await self._update_fields(
            intent_id,
            {
                "fulfilled_at": datetime.now(timezone.utc),
                "receipts": receipts,
            },
        )

    async def _update_fields(self, intent_id: UUID, fields: Dict[str, Any]) -> None:
        async with self._session_factory() as session:
            record = await session.get(OrderIntent, str(intent_id))
            if record is None:
                raise KeyError("intent not found")
            for key, value in fields.items():
                setattr(record, key, value)
            await session.commit()

    @staticmethod
    def _to_state(record: OrderIntent) -> IntentState:
        receipts = record.receipts or {}
        authorization_id = None
        if record.authorization_id:
            try:
                authorization_id = UUID(record.authorization_id)
            except ValueError:
                authorization_id = UUID(str(record.authorization_id))
        fulfilled_at = record.fulfilled_at
        return IntentState(
            intent_id=UUID(record.id),
            nonce=record.nonce,
            stripe_intent_id=record.stripe_intent_id,
            client_secret=record.client_secret,
            expires_at=record.expires_at,
            amount_cents=record.amount_cents,
            currency=record.currency,
            items=record.items,
            agent_id=record.agent_id,
            customer_id=record.customer_id,
            transcript_hash=record.transcript_hash,
            authorization_id=authorization_id,
            payment_reference=record.payment_reference,
            fulfilled_at=fulfilled_at,
            receipts=receipts,
        )
