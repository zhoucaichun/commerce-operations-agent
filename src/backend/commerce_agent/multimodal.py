"""Synthetic-only multimodal normalization; never reads or stores attachment bytes."""

from __future__ import annotations

from typing import Any


DEMO_SCENARIOS = {
    "macbook_charger": {"slots": {"device": "MacBook Air M2", "sku": "SKU005"}, "summary": "Synthetic image candidate: MacBook Air M2, USB-C 65W charger (SKU005).", "confidence": "high"},
    "order_screenshot": {"slots": {"order_id": "ORD-10023"}, "summary": "Synthetic OCR candidate: order ORD-10023. Identity suffix is still required.", "confidence": "medium"},
    "battery_damage": {"slots": {}, "summary": "Synthetic image safety signal: possible damaged or swollen battery.", "confidence": "high", "risk_reason": "attachment_battery_safety"},
    "voice_macbook": {"slots": {"device": "MacBook Air M2", "sku": "SKU005"}, "summary": "Synthetic transcription: Will SKU005 work with my MacBook Air M2?", "confidence": "high"},
}


def analyze_attachments(attachments: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not attachments:
        return None
    analyses = [DEMO_SCENARIOS.get(item.get("demo_scenario"), {"slots": {}, "summary": f"Unprocessed {item['kind']} metadata: {item['name']}. No file bytes were uploaded.", "confidence": "low"}) for item in attachments]
    risk = next((item.get("risk_reason") for item in analyses if item.get("risk_reason")), None)
    slots: dict[str, str] = {}
    for item in analyses:
        if item["confidence"] == "high":
            slots.update(item["slots"])
    return {"attachments": len(attachments), "summary": " ".join(item["summary"] for item in analyses), "confidence": "high" if slots else "low", "slots": slots, "risk_reason": risk, "mode": "synthetic_metadata_only"}
