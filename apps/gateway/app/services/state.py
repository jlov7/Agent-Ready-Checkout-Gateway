from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, cast
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
    items: list[dict[str, Any]]
    agent_id: str
    customer_id: str
    transcript_hash: str | None = None
    authorization_id: UUID | None = None
    payment_reference: str | None = None
    fulfilled_at: datetime | None = None
    receipts: dict[str, str] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= self.expires_at


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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
        items: list[dict[str, Any]],
        agent_id: str,
        customer_id: str,
    ) -> IntentState:
        intent_id = uuid4()
        nonce = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)

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

    async def set_fulfilled(self, intent_id: UUID, receipts: dict[str, str]) -> None:
        await self._update_fields(
            intent_id,
            {
                "fulfilled_at": datetime.now(UTC),
                "receipts": receipts,
            },
        )

    async def _update_fields(self, intent_id: UUID, fields: dict[str, Any]) -> None:
        async with self._session_factory() as session:
            record = await session.get(OrderIntent, str(intent_id))
            if record is None:
                raise KeyError("intent not found")
            for key, value in fields.items():
                setattr(record, key, value)
            await session.commit()

    @staticmethod
    def _to_state(record: OrderIntent) -> IntentState:
        receipts = cast(dict[str, str], record.receipts or {})
        authorization_id = None
        authorization_id_raw = cast(str | None, record.authorization_id)
        if authorization_id_raw:
            try:
                authorization_id = UUID(authorization_id_raw)
            except ValueError:
                authorization_id = UUID(str(authorization_id_raw))
        fulfilled_at = _as_utc(cast(datetime | None, record.fulfilled_at))
        return IntentState(
            intent_id=UUID(cast(str, record.id)),
            nonce=cast(str, record.nonce),
            stripe_intent_id=cast(str, record.stripe_intent_id),
            client_secret=cast(str, record.client_secret),
            expires_at=cast(datetime, _as_utc(cast(datetime, record.expires_at))),
            amount_cents=cast(int, record.amount_cents),
            currency=cast(str, record.currency),
            items=cast(list[dict[str, Any]], record.items),
            agent_id=cast(str, record.agent_id),
            customer_id=cast(str, record.customer_id),
            transcript_hash=cast(str | None, record.transcript_hash),
            authorization_id=authorization_id,
            payment_reference=cast(str | None, record.payment_reference),
            fulfilled_at=fulfilled_at,
            receipts=receipts,
        )
