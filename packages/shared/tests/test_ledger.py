from __future__ import annotations

import asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from packages.shared.shared.ledger.database import Base
from packages.shared.shared.ledger.service import ConsentLedgerService


def test_consent_ledger_chain_integrity(tmp_path):
    async def _run():
        database_url = f"sqlite+aiosqlite:///{tmp_path/'ledger.db'}"
        engine = create_async_engine(database_url, future=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        service = ConsentLedgerService(session_factory)

        intent_id = uuid4()
        for idx in range(3):
            await service.append_entry(
                intent_id=intent_id,
                transcript_hash=f"hash-{idx}",
                payload={"index": idx},
                customer_ip="127.0.0.1",
                user_agent="pytest",
            )

        is_valid = await service.verify_chain()
        assert is_valid

        await engine.dispose()

    asyncio.run(_run())
