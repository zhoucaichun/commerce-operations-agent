"""User-grounded slot updates; identity is never inferred by the model."""
from __future__ import annotations

import re
from typing import Any

SLOT_NAMES = {"device", "device_model", "country", "region", "budget", "budget_text",
              "usage_scenario", "category", "query", "sku", "order_id", "identity_suffix", "topic"}


def clean_slots(slots: dict[str, Any]) -> dict[str, str]:
    """Placeholder values are missing information, never usable tool inputs."""
    placeholders = {"", "unknown", "null", "none", "n/a", "undefined", "未知", "未提供", "不详"}
    return {key: str(value).strip()[:256] for key, value in slots.items()
            if key in SLOT_NAMES and isinstance(value, (str, int, float))
            and not isinstance(value, bool) and str(value).strip().lower() not in placeholders}


def explicit_slots(message: str) -> dict[str, str]:
    slots: dict[str, str] = {}
    patterns = {
        "order_id": r"\b((?:ORD|ORB)-\d{4,})\b",
        "sku": r"\b(AC-\d+W|CB-[A-Z0-9-]+|SKU\d{3}|SYN-[A-Z0-9-]+|SP-[A-Z0-9-]+|ORBIT-\d+W)\b",
        "device": r"\b(MacBook(?: (?:Air|Pro))?(?: (?:M\d|\d{2}))?|iPhone(?: \d{1,2})?(?: Pro)?|iPad(?: Pro)?|Samsung Galaxy S\d+|Google Pixel \d+|USB-C)\b",
        "identity_suffix": r"(?:后四位|suffix|last four|last 4)\s*[:：]?\s*([A-Za-z0-9]{4})\b",
        "budget": r"(?:预算\s*|\$|under\s*\$?|below\s*\$?)(\d+(?:\.\d+)?)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, message, re.I)
        if match:
            slots[key] = match.group(1).upper() if key in {"order_id", "sku"} else match.group(1)
    # A suffix-only continuation is allowed, but never take digits from an order ID.
    if "identity_suffix" not in slots:
        match = re.fullmatch(r"\s*([A-Za-z0-9]{4})\s*", message)
        if not match:
            match = re.search(r"(?:tracking|物流|轨迹).*?(?<![\w-])(\d{4})\s*$", message, re.I)
        if match:
            slots["identity_suffix"] = match.group(1)
    for region, pattern in {"US": r"美国|\bunited states\b|\bUS\b", "CN": r"中国|\bCN\b",
                            "EU": r"欧盟|\bEU\b", "UK": r"英国|\bUK\b"}.items():
        if re.search(pattern, message, re.I):
            slots["country"] = region
            slots["region"] = region
    return slots


def merge_slots(memory: dict[str, Any], message: str, supplied: dict[str, str], intent: str) -> dict[str, str]:
    current = {**explicit_slots(message), **clean_slots(supplied)}
    old = clean_slots(memory.get("slots", {}))
    # Business context does not follow a user into a different task family.
    previous = memory.get("intent")
    if intent != "unsupported" and previous and intent != previous:
        shared = {"device", "device_model", "country", "region", "usage_scenario"}
        old = {k: v for k, v in old.items() if k in shared}
    if current.get("order_id") and current["order_id"] != old.get("order_id"):
        old.pop("identity_suffix", None)
    if "device" in current:
        old.pop("device_model", None)
    if "device_model" in current:
        old.pop("device", None)
    if "budget" in current:
        old.pop("budget_text", None)
    return {**clean_slots(memory.get("preferences", {})), **old, **current}


def model_context(message: str, slots: dict[str, str]) -> tuple[str, dict[str, str]]:
    """Do not send the ownership suffix to a model or a persisted trace."""
    suffix = slots.get("identity_suffix")
    if suffix:
        message = message.replace(suffix, "[identity redacted]")
    message = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b\d{10,}\b|\bsk-[A-Za-z0-9_-]+", "[redacted]", message)
    safe_slots = {k: re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\b\d{10,}\b|\bsk-[A-Za-z0-9_-]+", "[redacted]", v)
                  for k, v in slots.items() if k != "identity_suffix"}
    return message, safe_slots
