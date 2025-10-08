# Langfuse Integration

This directory reserves space for future Langfuse configuration (e.g., API keys, dashboard exports).

When deploying Langfuse separately, update `.env` with `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_SECRET_KEY` and ensure the OTLP exporter in `otel/collector-config.yaml` forwards traces to your Langfuse instance.
