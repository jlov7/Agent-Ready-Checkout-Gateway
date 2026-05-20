from __future__ import annotations

from typing import cast

from fastapi import Depends, Request

from .context import AppContext


def get_context(request: Request) -> AppContext:
    return cast(AppContext, request.app.state.context)


def get_intent_store(context: AppContext = Depends(get_context)):
    return context.intent_store


def get_nonce_service(context: AppContext = Depends(get_context)):
    return context.nonce_service


def get_ledger_service(context: AppContext = Depends(get_context)):
    return context.ledger_service


def get_stripe_adapter(context: AppContext = Depends(get_context)):
    return context.stripe_adapter


def get_settings(context: AppContext = Depends(get_context)):
    return context.settings


def get_idempotency_service(context: AppContext = Depends(get_context)):
    return context.idempotency_service
