from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


@dataclass(frozen=True)
class GeneratedReceipt:
    png_path: Path
    pdf_path: Path
    manifest_path: Path


def _receipt_payload(
    *,
    order_id: str,
    items: list[dict[str, Any]],
    total: str,
    currency: str,
    transcript_hash: str,
    issued_at: datetime,
) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "items": items,
        "total": total,
        "currency": currency,
        "transcript_hash": transcript_hash,
        "issued_at": issued_at.isoformat(),
    }


def _write_png(path: Path, payload: dict[str, Any], digest: str) -> None:
    image = Image.new("RGB", (1000, 700), "white")
    draw = ImageDraw.Draw(image)
    lines = [
        "Agent-Ready Checkout Receipt",
        f"Order: {payload['order_id']}",
        f"Issued: {payload['issued_at']}",
        f"Total: {payload['total']} {payload['currency'].upper()}",
        f"Transcript: {payload['transcript_hash']}",
        f"Receipt digest: {digest}",
        "",
        "Items:",
    ]
    for item in payload["items"]:
        lines.append(f"- {item.get('sku', 'unknown')} x{item.get('qty', 1)}")

    y = 48
    for line in lines:
        draw.text((48, y), line, fill="black")
        y += 34
    image.save(path)


def _write_pdf(path: Path, payload: dict[str, Any], digest: str) -> None:
    doc = canvas.Canvas(str(path), pagesize=letter)
    _, height = letter
    y = height - 72
    lines = [
        "Agent-Ready Checkout Receipt",
        f"Order: {payload['order_id']}",
        f"Issued: {payload['issued_at']}",
        f"Total: {payload['total']} {payload['currency'].upper()}",
        f"Transcript: {payload['transcript_hash']}",
        f"Receipt digest: {digest}",
        "",
        "Items:",
    ]
    for item in payload["items"]:
        lines.append(f"- {item.get('sku', 'unknown')} x{item.get('qty', 1)}")

    for line in lines:
        doc.drawString(72, y, line)
        y -= 18
    doc.save()


def generate_receipts(
    *,
    order_id: str,
    items: list[dict[str, Any]],
    total: str,
    currency: str,
    transcript_hash: str,
    issued_at: datetime,
    output_dir: str,
    signing_cert: str | None = None,
    signing_key: str | None = None,
) -> GeneratedReceipt:
    if bool(signing_cert) != bool(signing_key):
        raise RuntimeError("C2PA signing requires both certificate and private key paths")

    payload = _receipt_payload(
        order_id=order_id,
        items=items,
        total=total,
        currency=currency,
        transcript_hash=transcript_hash,
        issued_at=issued_at,
    )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(encoded).hexdigest()

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{order_id}-{digest[:12]}"
    png_path = directory / f"{stem}.png"
    pdf_path = directory / f"{stem}.pdf"
    manifest_path = directory / f"{stem}.manifest.json"

    _write_png(png_path, payload, digest)
    _write_pdf(pdf_path, payload, digest)
    manifest_path.write_text(
        json.dumps(
            {
                "payload": payload,
                "digest": digest,
                "c2pa": {
                    "requested": bool(signing_cert and signing_key),
                    "status": "not_applied",
                    "reason": "Reference implementation emits a detached receipt manifest.",
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return GeneratedReceipt(png_path=png_path, pdf_path=pdf_path, manifest_path=manifest_path)
