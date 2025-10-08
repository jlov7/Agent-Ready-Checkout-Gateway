from __future__ import annotations

from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
except ImportError:  # pragma: no cover - optional dependency
    OTLPSpanExporter = None  # type: ignore

try:
    from langfuse.client import Langfuse
except ImportError:  # pragma: no cover - optional dependency during testing
    Langfuse = None  # type: ignore


def setup_tracing(service_name: str, endpoint: Optional[str]) -> None:
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    if endpoint and OTLPSpanExporter is not None:
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def build_langfuse(
    public_key: Optional[str], secret_key: Optional[str], host: Optional[str]
):  # pragma: no cover - simple factory
    if Langfuse is None or not public_key or not secret_key or not host:
        return None
    return Langfuse(public_key=public_key, secret_key=secret_key, host=host)
