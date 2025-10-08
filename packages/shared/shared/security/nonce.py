from __future__ import annotations

from cachetools import TTLCache


class NonceService:
    """In-memory nonce cache with TTL to prevent replay attacks."""

    def __init__(self, ttl_seconds: int, maxsize: int = 1024):
        self._cache: TTLCache[str, bool] = TTLCache(maxsize=maxsize, ttl=ttl_seconds)

    def is_unique(self, nonce: str) -> bool:
        if nonce in self._cache:
            return False
        self._cache[nonce] = True
        return True
