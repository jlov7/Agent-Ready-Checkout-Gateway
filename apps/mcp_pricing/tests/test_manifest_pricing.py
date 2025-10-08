from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def _load_app():
    module_path = Path(__file__).resolve().parents[1] / "app" / "main.py"
    spec = importlib.util.spec_from_file_location("mcp_pricing_main", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.app


def test_pricing_manifest_exposes_tool():
    app = _load_app()
    client = TestClient(app)
    response = client.get("/mcp/manifest")
    assert response.status_code == 200
    data = response.json()
    assert data["tools"][0]["name"] == "pricing.quote"
