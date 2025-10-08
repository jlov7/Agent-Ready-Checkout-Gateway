#!/usr/bin/env python
"""Regenerate the OpenAPI schema for the gateway."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.openapi.utils import get_openapi

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.gateway.main import create_app


def main() -> None:
    app = create_app()
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    output_path = Path("apps/gateway/openapi.json")
    output_path.write_text(json.dumps(openapi_schema, indent=2), encoding="utf-8")
    print(f"Wrote OpenAPI schema to {output_path}")


if __name__ == "__main__":
    main()
