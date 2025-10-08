FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY pyproject.toml README.md CHANGELOG.md ./

RUN pip install --upgrade pip setuptools wheel && \
    pip install ".[dev]"

COPY . .

EXPOSE 8080

CMD ["uvicorn", "apps.gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
