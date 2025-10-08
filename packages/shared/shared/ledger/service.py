from __future__ import annotations

import json
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..utils.crypto import sha256_hex
from .models import ConsentLedgerEntry


class ConsentLedgerService:
    """Append-only ledger with hash chaining."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def append_entry(
        self,
        *,
        intent_id: UUID,
        transcript_hash: str,
        payload: dict[str, Any],
        customer_ip: str | None,
        user_agent: str | None,
    ) -> ConsentLedgerEntry:
        async with self._session_factory() as session:
            previous_hash = await self._get_latest_entry_hash(session)
            canon_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            entry_hash = sha256_hex(
                f"{transcript_hash}|{previous_hash or ''}|{canon_payload}"
            )

            entry = ConsentLedgerEntry(
                id=str(uuid4()),
                intent_id=str(intent_id),
                transcript_hash=transcript_hash,
                previous_hash=previous_hash,
                entry_hash=entry_hash,
                payload=payload,
                customer_ip=customer_ip,
                user_agent=user_agent,
            )
            session.add(entry)
            await session.flush()
            await session.commit()
            return entry

    async def _get_latest_entry_hash(self, session: AsyncSession) -> Optional[str]:
        result = await session.execute(
            select(ConsentLedgerEntry.entry_hash).order_by(ConsentLedgerEntry.created_at.desc()).limit(1)
        )
        row = result.scalar_one_or_none()
        return row

    async def verify_chain(self) -> bool:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ConsentLedgerEntry).order_by(ConsentLedgerEntry.created_at.asc())
            )
            previous_hash = None
            for entry in result.scalars():
                canon_payload = json.dumps(entry.payload, sort_keys=True, separators=(",", ":"))
                expected_hash = sha256_hex(
                    f"{entry.transcript_hash}|{previous_hash or ''}|{canon_payload}"
                )
                if expected_hash != entry.entry_hash:
                    return False
                previous_hash = entry.entry_hash
            return True
