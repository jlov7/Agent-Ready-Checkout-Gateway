from __future__ import annotations

from typing import Callable

from fastapi import FastAPI, Response
from fastapi.middleware.gzip import GZipMiddleware
from starlette.requests import Request

from packages.shared.shared.logging.setup import bind_context, reset_context

from .app.api.routes import router as api_router
from .app.core.lifespan import lifespan


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agent-Ready Checkout Gateway",
        version="0.1.0",
        description="ACP-compliant gateway for agent-initiated ecommerce orders.",
        lifespan=lifespan,
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable):
        bind_context(path=request.url.path, method=request.method)
        try:
            response: Response = await call_next(request)
        finally:
            reset_context()

        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.get("/health/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def ready(request: Request) -> dict[str, str]:
        context = request.app.state.context  # type: ignore[attr-defined]
        ready_checks = {
            "stripe": bool(context.stripe_adapter),
            "ledger": True,
            "langfuse": bool(context.langfuse_client),
        }
        return {"status": "ok", "checks": ready_checks}

    app.include_router(api_router)
    return app


app = create_app()
