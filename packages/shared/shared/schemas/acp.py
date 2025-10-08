from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, model_validator, validator


class ToolCall(BaseModel):
    type: str = Field(..., description="Tool or action identifier")
    tool_call_id: UUID = Field(..., description="Unique identifier for the tool invocation")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: List[Dict[str, Any]] = Field(default_factory=list)


class Intent(BaseModel):
    id: UUID
    expires_at: datetime
    actions: List[ToolCall] = Field(default_factory=list)

    @validator("expires_at")
    def _ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("expires_at must include timezone information")
        return value


class Confirmation(BaseModel):
    method: str
    timestamp: datetime
    channel: str | None = None
    agent_user: str | None = None
    human_remark: str | None = None

    @validator("timestamp")
    def _ensure_timestamp_tz(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include timezone information")
        return value


class Signature(BaseModel):
    alg: str
    nonce: str
    value: str


class ACPTranscript(BaseModel):
    agent_id: HttpUrl
    customer_id: HttpUrl
    intent: Intent
    confirmation: Confirmation
    signature: Signature
    version: str = "1.0"

    @model_validator(mode="after")
    def _intent_not_expired(cls, values: "ACPTranscript") -> "ACPTranscript":
        expires_at: datetime = values.intent.expires_at
        now = datetime.now(timezone.utc)
        if expires_at < now:
            raise ValueError("intent has expired")
        return values
