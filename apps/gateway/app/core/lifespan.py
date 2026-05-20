from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
except ImportError:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore
    _rate_limit_exceeded_handler = None  # type: ignore

    class RateLimitExceeded(RuntimeError):  # type: ignore
        pass

    class SlowAPIMiddleware:  # type: ignore
        pass


from packages.shared.shared.config.settings import get_settings
from packages.shared.shared.logging.setup import configure_logging

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
except ImportError:  # pragma: no cover - optional dependencies
    FastAPIInstrumentor = None  # type: ignore
    HTTPXClientInstrumentor = None  # type: ignore

from packages.shared.shared.idempotency.service import IdempotencyService
from packages.shared.shared.ledger.service import ConsentLedgerService
from packages.shared.shared.observability.tracing import build_langfuse, setup_tracing
from packages.shared.shared.security.nonce import NonceService

from ..db.session import get_session_factory, init_db
from ..services.state import IntentStore
from .context import AppContext

TRUSTED_PROXY_HEADERS = ("x-forwarded-for", "x-real-ip")


def _rate_limit_key(request: Any) -> str:
    for header in TRUSTED_PROXY_HEADERS:
        forwarded = request.headers.get(header)
        if forwarded:
            return cast(str, forwarded.split(",")[0].strip())
    if request.client:
        return cast(str, request.client.host)
    return "global"


class _NoopLimiter:
    def limit(self, value):  # pragma: no cover - fallback
        def decorator(handler):
            return handler

        return decorator


limiter = (
    Limiter(key_func=_rate_limit_key, config_filename=".env.example")
    if Limiter is not None
    else _NoopLimiter()
)
_FASTAPI_INSTRUMENTED = False
_HTTPX_INSTRUMENTED = False


class _StubStripeAdapter:
    def __init__(self, reason: str):
        self._reason = reason

    async def create_payment_intent(self, *args, **kwargs):  # pragma: no cover - fallback
        raise RuntimeError(self._reason)

    async def confirm_payment(self, *args, **kwargs):  # pragma: no cover - fallback
        raise RuntimeError(self._reason)

    async def capture_payment(self, *args, **kwargs):  # pragma: no cover - fallback
        raise RuntimeError(self._reason)


def configure_middlewares(app: FastAPI, settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if Limiter is not None:
        app.add_middleware(SlowAPIMiddleware)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    if settings.app_env.lower() != "development":
        app.add_middleware(HTTPSRedirectMiddleware)
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


def configure_instrumentation(app: FastAPI) -> None:
    global _FASTAPI_INSTRUMENTED
    if FastAPIInstrumentor is not None and not _FASTAPI_INSTRUMENTED:
        FastAPIInstrumentor().instrument_app(app)
        _FASTAPI_INSTRUMENTED = True


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    setup_tracing("gateway", settings.otel_exporter_otlp_endpoint)

    global _HTTPX_INSTRUMENTED
    if HTTPXClientInstrumentor is not None and not _HTTPX_INSTRUMENTED:
        HTTPXClientInstrumentor().instrument()
        _HTTPX_INSTRUMENTED = True
    langfuse_client = build_langfuse(
        settings.langfuse_public_key, settings.langfuse_secret_key, settings.langfuse_host
    )

    await init_db()
    session_factory = get_session_factory()

    intent_store = IntentStore(session_factory)
    nonce_service = NonceService(settings.nonce_ttl_seconds)
    ledger_service = ConsentLedgerService(session_factory)
    idempotency_service = IdempotencyService(session_factory)

    from packages.shared.shared.psp.stripe_adapter import StripeAdapter

    try:
        stripe_adapter: object = StripeAdapter(settings.stripe_api_key)
    except RuntimeError as exc:
        if settings.app_env.lower() in {"development", "test"}:
            stripe_adapter = _StubStripeAdapter(str(exc))
        else:
            raise
    context = AppContext(
        settings=settings,
        intent_store=intent_store,
        nonce_service=nonce_service,
        ledger_service=ledger_service,
        stripe_adapter=stripe_adapter,
        langfuse_client=langfuse_client,
        idempotency_service=idempotency_service,
        session_factory=session_factory,
    )

    app.state.context = context

    yield
