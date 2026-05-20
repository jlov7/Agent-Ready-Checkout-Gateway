from __future__ import annotations

import json
from typing import Any, cast

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..utils.crypto import sha256_hex
from .models import IdempotencyRecord


class IdempotencyService:
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    async def check_existing(
        self, *, key: str, endpoint: str, payload: dict[str, Any]
    ) -> str | None:
        payload_hash = self._hash(payload)
        async with self._session_factory() as session:
            stmt = select(IdempotencyRecord).where(
                and_(IdempotencyRecord.key == key, IdempotencyRecord.endpoint == endpoint)
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            if record is None:
                return None
            if record.payload_hash != payload_hash:
                raise ValueError("idempotency payload mismatch")
            return cast(str, record.response_body)

    async def store(
        self, *, key: str, endpoint: str, payload: dict[str, Any], response: dict[str, Any]
    ) -> None:
        payload_hash = self._hash(payload)
        body = json.dumps(response, sort_keys=True)
        async with self._session_factory() as session:
            record = IdempotencyRecord(
                key=key,
                endpoint=endpoint,
                payload_hash=payload_hash,
                response_body=body,
            )
            await session.merge(record)
            await session.commit()

    def _hash(self, payload: dict[str, Any]) -> str:
        return sha256_hex(json.dumps(payload, sort_keys=True, separators=(",", ":")))
