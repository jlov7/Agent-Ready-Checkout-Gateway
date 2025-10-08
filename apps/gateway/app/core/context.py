from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import async_sessionmaker
from packages.shared.shared.config.settings import AppSettings
from packages.shared.shared.ledger.database import Base
from packages.shared.shared.ledger.service import ConsentLedgerService
from packages.shared.shared.observability.tracing import build_langfuse
from packages.shared.shared.psp.stripe_adapter import StripeAdapter
from packages.shared.shared.security.nonce import NonceService

from ..services.state import IntentStore


@dataclass
class AppContext:
    settings: AppSettings
    intent_store: IntentStore
    nonce_service: NonceService
    ledger_service: ConsentLedgerService
    stripe_adapter: StripeAdapter
    langfuse_client: object | None
    session_factory: async_sessionmaker
    base_model = Base
