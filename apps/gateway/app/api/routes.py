from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import urlparse
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from opentelemetry import trace

from packages.shared.shared.observability.langfuse import emit_trace
from packages.shared.shared.receipts.generator import generate_receipts
from packages.shared.shared.schemas.api import (
    AuthorizeRequest,
    AuthorizeResponse,
    ConfirmRequest,
    ConfirmResponse,
    FulfilRequest,
    FulfilResponse,
    IntentCreateRequest,
    IntentCreateResponse,
)
from packages.shared.shared.security.signatures import (
    HMACSignatureProvider,
    canonicalize_transcript,
    compute_transcript_hash,
)

from ..core.deps import (
    get_context,
    get_intent_store,
    get_ledger_service,
    get_idempotency_service,
    get_nonce_service,
    get_settings,
    get_stripe_adapter,
)
from ..core.lifespan import limiter
from ..services.state import IntentStore
from ..policies.policy_hook import PolicyDecision, PolicyInput, evaluate_policy


router = APIRouter(prefix="/api/v1")
tracer = trace.get_tracer(__name__)


def _rate_limit_value(request: Request) -> str:
    context = request.app.state.context  # type: ignore[attr-defined]
    return f"{context.settings.rate_limit_per_minute}/minute"


def _extract_agent_domain(agent_id: str) -> str:
    parsed = urlparse(agent_id)
    return parsed.hostname or parsed.netloc


@router.post(
    "/intents",
    response_model=IntentCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(lambda request: _rate_limit_value(request))
async def create_intent(
    payload: IntentCreateRequest,
    store: IntentStore = Depends(get_intent_store),
    stripe_adapter=Depends(get_stripe_adapter),
    settings=Depends(get_settings),
    context=Depends(get_context),
):
    with tracer.start_as_current_span("gateway.create_intent") as span:
        if settings.allowed_agent_domains:
            domain = _extract_agent_domain(payload.agent_id)
            if not any(domain.endswith(allowed) for allowed in settings.allowed_agent_domains):
                span.set_attribute("gateway.agent_domain_allowed", False)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="agent domain not allowed",
                )

        amount_cents = int(payload.max_total * 100)
        metadata = {
            "agent_id": payload.agent_id,
            "customer_id": payload.customer_id,
            "cart": payload.cart,
        }
        span.set_attribute("gateway.amount_cents", amount_cents)
        intent = await stripe_adapter.create_payment_intent(
            amount_cents=amount_cents, currency=payload.currency, metadata=metadata
        )

        state = await store.create(
            amount_cents=amount_cents,
            currency=payload.currency,
            stripe_intent_id=intent["id"],
            client_secret=intent["client_secret"],
            ttl_seconds=settings.nonce_ttl_seconds,
            items=payload.cart.get("items", []),
            agent_id=payload.agent_id,
            customer_id=payload.customer_id,
        )

        emit_trace(
            context.langfuse_client,
            name="create_intent",
            input=metadata,
            output={"intent_id": str(state.intent_id)},
        )

        return IntentCreateResponse(
            intent_id=state.intent_id,
            nonce=state.nonce,
            client_secret=state.client_secret,
            expires_at=state.expires_at,
        )


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_intent(
    request: Request,
    payload: ConfirmRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    store: IntentStore = Depends(get_intent_store),
    nonce_service=Depends(get_nonce_service),
    ledger_service=Depends(get_ledger_service),
    settings=Depends(get_settings),
    context=Depends(get_context),
    idempotency_service=Depends(get_idempotency_service),
):
    with tracer.start_as_current_span("gateway.confirm_intent") as span:
        payload_dict = payload.model_dump(mode="json")
        if idempotency_key:
            try:
                cached = await idempotency_service.check_existing(
                    key=idempotency_key, endpoint="confirm", payload=payload_dict
                )
            except ValueError:
                raise HTTPException(status_code=409, detail="idempotency conflict")
            if cached:
                return ConfirmResponse(**json.loads(cached))

        state = await store.get(payload.intent_id)

        transcript = payload.transcript
        if transcript.intent.id != payload.intent_id:
            raise HTTPException(status_code=400, detail="intent mismatch in transcript")
        if transcript.signature.nonce != state.nonce:
            raise HTTPException(status_code=400, detail="nonce mismatch")
        if not nonce_service.is_unique(transcript.signature.nonce):
            raise HTTPException(status_code=409, detail="nonce replay detected")

        signature_provider = HMACSignatureProvider(secret=settings.hmac_webhook_secret)

        raw_transcript = transcript.model_dump()
        transcript_for_signature = deepcopy(raw_transcript)
        transcript_for_signature["signature"]["value"] = ""
        canonical_transcript = canonicalize_transcript(transcript_for_signature)
        if not signature_provider.verify(
            payload=canonical_transcript,
            nonce=transcript.signature.nonce,
            signature=transcript.signature.value,
        ):
            raise HTTPException(status_code=401, detail="invalid signature")

        transcript_hash = compute_transcript_hash(raw_transcript)
        effective_ip = payload.customer_ip or (request.client.host if request.client else None)
        effective_ua = payload.user_agent or request.headers.get("user-agent")
        metadata: Dict[str, Any] = {
            "agent_id": transcript.agent_id,
            "customer_id": transcript.customer_id,
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
            "customer_ip": effective_ip,
            "user_agent": effective_ua,
        }

        entry = await ledger_service.append_entry(
            intent_id=payload.intent_id,
            transcript_hash=transcript_hash,
            payload={"transcript": raw_transcript, "metadata": metadata},
            customer_ip=effective_ip,
            user_agent=effective_ua,
        )
        await store.set_transcript_hash(payload.intent_id, transcript_hash)

        emit_trace(
            context.langfuse_client,
            name="confirm_intent",
            input=metadata,
            output={"ledger_entry_id": entry.id},
        )

        span.set_attribute("gateway.ledger_entry_id", entry.id)

        response = ConfirmResponse(
            confirmed_at=entry.created_at,
            ledger_entry_id=UUID(entry.id),
            transcript_hash=transcript_hash,
        )

        if idempotency_key:
            await idempotency_service.store(
                key=idempotency_key,
                endpoint="confirm",
                payload=payload_dict,
                response=response.model_dump(mode="json"),
            )

        return response


@router.post("/authorize", response_model=AuthorizeResponse)
async def authorize_payment(
    request: Request,
    payload: AuthorizeRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    store: IntentStore = Depends(get_intent_store),
    stripe_adapter=Depends(get_stripe_adapter),
    context=Depends(get_context),
    idempotency_service=Depends(get_idempotency_service),
):
    with tracer.start_as_current_span("gateway.authorize_payment") as span:
        payload_dict = payload.model_dump(mode="json")
        if idempotency_key:
            try:
                cached = await idempotency_service.check_existing(
                    key=idempotency_key, endpoint="authorize", payload=payload_dict
                )
            except ValueError:
                raise HTTPException(status_code=409, detail="idempotency conflict")
            if cached:
                return AuthorizeResponse(**json.loads(cached))

        state = await store.get(payload.intent_id)
        if not state.transcript_hash:
            raise HTTPException(status_code=409, detail="intent not confirmed")
        if state.transcript_hash != payload.transcript_hash:
            raise HTTPException(status_code=400, detail="transcript hash mismatch")

        risk_signals = {
            "user_agent": request.headers.get("user-agent"),
            "customer_ip": request.client.host if request.client else None,
        }

        policy_input = PolicyInput(
            intent_id=str(payload.intent_id),
            agent_id=state.agent_id,
            customer_id=state.customer_id,
            amount_cents=state.amount_cents,
            currency=state.currency,
            risk_signals=risk_signals,
        )
        policy_result = evaluate_policy(policy_input)
        if policy_result.decision == PolicyDecision.DENY:
            raise HTTPException(status_code=403, detail={"reasons": policy_result.reasons})

        intent = await stripe_adapter.confirm_payment(
            intent_id=state.stripe_intent_id,
            payment_method_token=payload.payment_method_token,
        )
        authorization_id = uuid4()
        payment_reference = intent.get("charges", {}).get("data", [{}])[0].get("id", intent["id"])
        await store.set_authorization(payload.intent_id, authorization_id, payment_reference)

        span.set_attribute("gateway.authorization_id", str(authorization_id))
        emit_trace(
            context.langfuse_client,
            name="authorize_payment",
            input={"intent_id": str(payload.intent_id)},
            output={"authorization_id": str(authorization_id)},
        )

        response = AuthorizeResponse(
            authorization_id=authorization_id,
            payment_reference=payment_reference,
            amount_cents=state.amount_cents,
            currency=state.currency,
            captured=intent.get("status") == "succeeded",
            policy_decision=policy_result.decision.value,
            policy_reasons=policy_result.reasons,
        )

        if idempotency_key:
            await idempotency_service.store(
                key=idempotency_key,
                endpoint="authorize",
                payload=payload_dict,
                response=response.model_dump(mode="json"),
            )

        return response


@router.post("/fulfil", response_model=FulfilResponse)
async def fulfil_order(
    payload: FulfilRequest,
    store: IntentStore = Depends(get_intent_store),
    settings=Depends(get_settings),
    context=Depends(get_context),
):
    with tracer.start_as_current_span("gateway.fulfil_order") as span:
        state = await store.get(payload.intent_id)
        if state.authorization_id != payload.authorization_id:
            raise HTTPException(status_code=400, detail="authorization mismatch")
        if state.receipts:
            raise HTTPException(status_code=409, detail="order already fulfilled")

        issued_at = datetime.now(timezone.utc)
        try:
            receipt = generate_receipts(
                order_id=str(payload.intent_id),
                items=[{"sku": item.get("sku"), "qty": item.get("quantity")} for item in state.items],
                total=f"{state.amount_cents/100:.2f}",
                currency=state.currency,
                transcript_hash=state.transcript_hash or "",
                issued_at=issued_at,
                output_dir="receipts",
                signing_cert=settings.c2pa_signing_cert_path,
                signing_key=settings.c2pa_signing_key_path,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        await store.set_fulfilled(
            payload.intent_id,
            receipts={
                "png": str(receipt.png_path),
                "pdf": str(receipt.pdf_path),
            },
        )

        emit_trace(
            context.langfuse_client,
            name="fulfil_order",
            input={"authorization_id": str(payload.authorization_id)},
            output={"receipt_png": str(receipt.png_path)},
        )

        span.set_attribute("gateway.receipt_png", str(receipt.png_path))

        return FulfilResponse(
            fulfilment_id=uuid4(),
            receipt_png_path=str(receipt.png_path),
            receipt_pdf_path=str(receipt.pdf_path),
            transcript_hash=state.transcript_hash or "",
            issued_at=issued_at,
        )
