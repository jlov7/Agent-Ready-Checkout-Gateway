from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ToolCall(BaseModel):
    type: str = Field(..., description="Tool or action identifier")
    tool_call_id: UUID = Field(..., description="Unique identifier for the tool invocation")
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: list[dict[str, Any]] = Field(default_factory=list)


class Intent(BaseModel):
    id: UUID
    expires_at: datetime
    actions: list[ToolCall] = Field(default_factory=list)

    @field_validator("expires_at")
    @classmethod
    def _ensure_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("expires_at must include timezone information")
        if value < datetime.now(UTC):
            raise ValueError("intent has expired")
        return value


class Confirmation(BaseModel):
    method: str
    timestamp: datetime
    channel: str | None = None
    agent_user: str | None = None
    human_remark: str | None = None

    @field_validator("timestamp")
    @classmethod
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
