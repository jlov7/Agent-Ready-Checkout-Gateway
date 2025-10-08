from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field, HttpUrl, PostgresDsn, model_validator

load_dotenv(".env")


class AppSettings(BaseModel):
    """Application-level settings loaded from environment variables."""

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    gateway_host: str = Field(default="0.0.0.0", alias="GATEWAY_HOST")
    gateway_port: int = Field(default=8080, alias="GATEWAY_PORT")
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://gateway:gateway@localhost:5432/gateway",
        alias="DATABASE_URL",
    )
    nonce_ttl_seconds: int = Field(default=600, alias="NONCE_TTL_SECONDS")
    rate_limit_per_minute: int = Field(default=30, alias="RATE_LIMIT_PER_MINUTE")
    allowed_agent_domains: List[str] = Field(default_factory=list, alias="ALLOWED_AGENT_DOMAINS")

    stripe_api_key: str = Field(default="sk_test_placeholder", alias="STRIPE_API_KEY")
    stripe_webhook_secret: str = Field(default="whsec_placeholder", alias="STRIPE_WEBHOOK_SECRET")

    langfuse_host: HttpUrl | None = Field(default=None, alias="LANGFUSE_HOST")
    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")

    otel_exporter_otlp_endpoint: HttpUrl | None = Field(
        default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )

    c2pa_signing_cert_path: str | None = Field(default=None, alias="C2PA_SIGNING_CERT_PATH")
    c2pa_signing_key_path: str | None = Field(default=None, alias="C2PA_SIGNING_KEY_PATH")

    hmac_webhook_secret: str = Field(default="whsec_hmac_placeholder", alias="HMAC_WEBHOOK_SECRET")

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }

    @model_validator(mode="before")
    def _split_allowed_domains(cls, values: dict[str, str]) -> dict[str, str]:
        domains = values.get("ALLOWED_AGENT_DOMAINS") or values.get("allowed_agent_domains")
        if isinstance(domains, str):
            values["ALLOWED_AGENT_DOMAINS"] = [d.strip() for d in domains.split(",") if d.strip()]
        return values


def _env_overrides() -> dict[str, str]:
    overrides: dict[str, str] = {}
    for field_name, field in AppSettings.model_fields.items():
        alias = field.alias or field_name
        value = os.getenv(alias)
        if value is not None:
            overrides[field_name] = value
    return overrides


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    data = _env_overrides()
    return AppSettings(**data)
