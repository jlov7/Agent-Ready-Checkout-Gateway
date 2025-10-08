from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from packages.shared.shared.utils.crypto import compute_hmac


GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8080/api/v1")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://localhost:8100")
PRICING_URL = os.getenv("PRICING_URL", "http://localhost:8200")
HMAC_SECRET = os.getenv("HMAC_WEBHOOK_SECRET", "secret123")


class OrderState(TypedDict, total=False):
    cart: Dict[str, Any]
    intent: Dict[str, Any]
    confirmation: Dict[str, Any]
    authorization: Dict[str, Any]
    fulfilment: Dict[str, Any]


@dataclass
class AgentConfig:
    agent_id: str = "https://agents.example.com/mock-agent"
    customer_id: str = "https://customers.example.com/demo-user"
    currency: str = "usd"


async def fetch_inventory(client: httpx.AsyncClient, sku: str) -> Dict[str, Any]:
    resp = await client.get(f"{INVENTORY_URL}/inventory/{sku}")
    resp.raise_for_status()
    return resp.json()


async def fetch_price(client: httpx.AsyncClient, sku: str) -> Dict[str, Any]:
    resp = await client.get(f"{PRICING_URL}/pricing/{sku}")
    resp.raise_for_status()
    return resp.json()


async def node_build_cart(state: OrderState, config: AgentConfig, client: httpx.AsyncClient) -> OrderState:
    sku = state.get("cart", {}).get("sku", "SKU123")
    inventory = await fetch_inventory(client, sku)
    price = await fetch_price(client, sku)
    cart = {
        "items": [
            {
                "sku": sku,
                "name": inventory.get("name"),
                "quantity": 1,
                "unit_price_cents": price.get("price", {}).get("unit_price", price.get("unit_price", 0)),
            }
        ]
    }
    state["cart"] = cart
    return state


async def node_create_intent(state: OrderState, config: AgentConfig, client: httpx.AsyncClient) -> OrderState:
    cart = state["cart"]
    max_total = sum(item["unit_price_cents"] for item in cart["items"]) / 100
    resp = await client.post(
        f"{GATEWAY_URL}/intents",
        json={
            "agent_id": config.agent_id,
            "customer_id": config.customer_id,
            "cart": cart,
            "max_total": max_total,
            "currency": config.currency,
        },
    )
    resp.raise_for_status()
    state["intent"] = resp.json()
    return state


async def node_confirm(state: OrderState, config: AgentConfig, client: httpx.AsyncClient) -> OrderState:
    intent = state["intent"]
    nonce = intent["nonce"]
    intent_id = intent["intent_id"]
    print(f"Order preview for {config.customer_id}:")
    for item in state["cart"]["items"]:
        print(f"  - {item['sku']} x{item['quantity']} @ {item['unit_price_cents']/100:.2f}")
    confirmation = input("Approve order? (y/N): ").strip().lower() == "y"
    if not confirmation:
        raise RuntimeError("Order not approved by human operator.")

    transcript = {
        "agent_id": config.agent_id,
        "customer_id": config.customer_id,
        "intent": {
            "id": intent_id,
            "expires_at": intent["expires_at"],
            "actions": [],
        },
        "confirmation": {
            "method": "human",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": "cli",
            "human_remark": "Approved via mock agent CLI",
        },
        "signature": {
            "alg": "HS256",
            "nonce": nonce,
            "value": "",
        },
        "version": "1.0",
    }
    sanitized = json.loads(json.dumps(transcript))
    sanitized["signature"]["value"] = ""
    canonical = json.dumps(sanitized, sort_keys=True, separators=(",", ":"))
    signature = compute_hmac(HMAC_SECRET, f"{nonce}:{canonical}")
    transcript["signature"]["value"] = signature

    resp = await client.post(
        f"{GATEWAY_URL}/confirm",
        json={
            "intent_id": intent_id,
            "transcript": transcript,
            "customer_ip": "127.0.0.1",
            "user_agent": "mock-agent-cli",
        },
    )
    resp.raise_for_status()
    state["confirmation"] = resp.json()
    return state


async def node_authorize(state: OrderState, config: AgentConfig, client: httpx.AsyncClient) -> OrderState:
    intent = state["intent"]["intent_id"]
    transcript_hash = state["confirmation"]["transcript_hash"]
    resp = await client.post(
        f"{GATEWAY_URL}/authorize",
        json={
            "intent_id": intent,
            "transcript_hash": transcript_hash,
            "payment_method_token": "pm_card_visa",
        },
    )
    resp.raise_for_status()
    state["authorization"] = resp.json()
    return state


async def node_fulfil(state: OrderState, config: AgentConfig, client: httpx.AsyncClient) -> OrderState:
    intent = state["intent"]["intent_id"]
    authorization = state["authorization"]["authorization_id"]
    resp = await client.post(
        f"{GATEWAY_URL}/fulfil",
        json={
            "intent_id": intent,
            "authorization_id": authorization,
            "fulfillment_reference": "MOCK-SHIPMENT",
        },
    )
    resp.raise_for_status()
    state["fulfilment"] = resp.json()
    return state


async def run_demo() -> OrderState:
    config = AgentConfig()
    graph = StateGraph(OrderState)

    async with httpx.AsyncClient(timeout=10) as client:
        graph.add_node("build_cart", lambda state: node_build_cart(state, config, client))
        graph.add_node("create_intent", lambda state: node_create_intent(state, config, client))
        graph.add_node("confirm", lambda state: node_confirm(state, config, client))
        graph.add_node("authorize", lambda state: node_authorize(state, config, client))
        graph.add_node("fulfil", lambda state: node_fulfil(state, config, client))

        graph.set_entry_point("build_cart")
        graph.add_edge("build_cart", "create_intent")
        graph.add_edge("create_intent", "confirm")
        graph.add_edge("confirm", "authorize")
        graph.add_edge("authorize", "fulfil")
        graph.add_edge("fulfil", END)

        compiled = graph.compile()
        final_state = await compiled.ainvoke({})
        return final_state


if __name__ == "__main__":
    asyncio.run(run_demo())
