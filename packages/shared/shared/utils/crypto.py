from __future__ import annotations

import hashlib
import hmac


def sha256_hex(data: str | bytes) -> str:
    payload = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(payload).hexdigest()


def compute_hmac(secret: str, payload: str | bytes) -> str:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    return hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()
