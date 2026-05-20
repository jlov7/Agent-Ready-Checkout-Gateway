from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from packages.shared.shared.utils.data import load_pricing

PRICING_PATH = os.getenv("PRICING_DATA_PATH", "scripts/fixtures/pricing.json")


class PricingRequest(BaseModel):
    skus: list[str]


app = FastAPI(title="MCP Pricing Server", version="0.1.0")


def _load_pricing() -> dict[str, Any]:
    return load_pricing(PRICING_PATH)


@app.get("/mcp/manifest")
async def manifest() -> dict[str, Any]:
    return {
        "schema": "https://modelcontextprotocol.io/manifest/schema.json",
        "name": "pricing",
        "description": "Pricing lookup tools for agent-ready checkout",
        "tools": [
            {
                "name": "pricing.quote",
                "description": "Get price quotes for the given SKUs",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "skus": {
                            "type": "array",
                            "items": {"type": "string"},
                        }
                    },
                    "required": ["skus"],
                },
            }
        ],
    }


@app.post("/mcp/tools/pricing.quote")
async def pricing_quote(payload: PricingRequest) -> dict[str, Any]:
    pricing = _load_pricing()
    result = {sku: pricing.get(sku) for sku in payload.skus if sku in pricing}
    return {"prices": result}


@app.get("/pricing/{sku}")
async def get_price(sku: str) -> dict[str, Any]:
    pricing = _load_pricing()
    if sku not in pricing:
        raise HTTPException(status_code=404, detail="SKU not found")
    return {"sku": sku, "price": pricing[sku]}
