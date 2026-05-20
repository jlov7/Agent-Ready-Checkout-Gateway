from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from packages.shared.shared.utils.data import load_inventory

INVENTORY_PATH = os.getenv("INVENTORY_DATA_PATH", "scripts/fixtures/inventory.json")


class InventoryRequest(BaseModel):
    skus: list[str]


app = FastAPI(title="MCP Inventory Server", version="0.1.0")


def _load_inventory() -> list[dict[str, Any]]:
    return load_inventory(INVENTORY_PATH)


@app.get("/mcp/manifest")
async def manifest() -> dict[str, Any]:
    return {
        "schema": "https://modelcontextprotocol.io/manifest/schema.json",
        "name": "inventory",
        "description": "Inventory lookup tools for agent-ready checkout",
        "tools": [
            {
                "name": "inventory.lookup",
                "description": "Retrieve inventory availability by SKU",
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


@app.post("/mcp/tools/inventory.lookup")
async def inventory_lookup(payload: InventoryRequest) -> dict[str, Any]:
    inventory = _load_inventory()
    index = {item["sku"]: item for item in inventory}
    result = []
    for sku in payload.skus:
        item = index.get(sku)
        if item:
            result.append(item)
    return {"items": result}


@app.get("/inventory/{sku}")
async def get_inventory(sku: str) -> dict[str, Any]:
    inventory = _load_inventory()
    for item in inventory:
        if item["sku"] == sku:
            return item
    raise HTTPException(status_code=404, detail="SKU not found")
