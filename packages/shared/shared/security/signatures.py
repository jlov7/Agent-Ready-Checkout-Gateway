from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

import hmac

from ..utils.crypto import compute_hmac, sha256_hex


class SignatureProvider(Protocol):
    def verify(self, *, payload: str, nonce: str, signature: str) -> bool:
        ...


@dataclass
class HMACSignatureProvider:
    secret: str

    def verify(self, *, payload: str, nonce: str, signature: str) -> bool:
        canonical = f"{nonce}:{payload}"
        expected = compute_hmac(self.secret, canonical)
        provided = signature.lower()
        return hmac_compare(expected, provided)


def canonicalize_transcript(transcript: dict) -> str:
    """Return canonical JSON string for hashing/signing."""
    import json

    return json.dumps(transcript, sort_keys=True, separators=(",", ":"))


def compute_transcript_hash(transcript: dict) -> str:
    return sha256_hex(canonicalize_transcript(transcript))


def hmac_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
