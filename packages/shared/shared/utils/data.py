from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


def load_json(path: str | Path, default: Any) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return default
    with file_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def load_inventory(path: str | Path) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], load_json(path, default=[]))


def load_pricing(path: str | Path) -> dict[str, Any]:
    return cast(dict[str, Any], load_json(path, default={}))
