"""A larger, reproducible merchant-like catalogue for local RAG and demos.

All rows are generated in-process from transparent templates.  They are not a
copy of a retailer catalogue, do not represent stock, and must never be shown
as live merchant facts.
"""

from __future__ import annotations

from typing import Any


def load_synthetic_merchant_products() -> list[dict[str, Any]]:
    """Return 216 deterministic synthetic 3C accessory records.

    The migrated Dify CSV remains useful as a small reviewed seed.  This
    larger corpus intentionally varies category, power, regional availability,
    device fit and usage language so retrieval and evaluation do not overfit to
    a few dozen hand-written rows.
    """
    families = (
        ("charger", "CHG", "VoltPath", (20, 30, 45, 65, 100, 140), ("USB-C",), "charging", "wall charger"),
        ("cable", "CBL", "LinkForge", (30, 60, 100, 140, 240, 480), ("USB-C", "USB-C"), "charging transfer", "usb-c cable"),
        ("hub", "HUB", "DockNest", (60, 85, 100, 140, 180, 240), ("USB-C", "HDMI", "USB-A"), "desk travel", "usb-c hub"),
        ("power_bank", "PBK", "ReserveGo", (20, 30, 45, 65, 100, 140), ("USB-C", "USB-A"), "travel emergency", "power bank"),
        ("audio", "AUD", "SoundLoop", (10, 15, 20, 25, 30, 45), ("USB-C", "Bluetooth"), "calls commute", "wireless audio"),
        ("storage", "SSD", "DataTrail", (10, 20, 30, 45, 65, 100), ("USB-C",), "backup creator", "portable storage"),
    )
    device_profiles = (
        ("iPhone 15 USB-C", "phone travel"),
        ("MacBook Air M2 USB-C", "laptop desk"),
        ("iPad Pro USB-C", "tablet creator"),
        ("Samsung Galaxy S24 USB-C", "android travel"),
        ("Google Pixel 8 USB-C", "android commute"),
        ("USB-C PD device", "universal daily"),
    )
    regions = (("US", "EU"), ("US", "JP"), ("EU", "UK"), ("US", "CA"), ("AU", "SG"), ("CN", "US", "EU"))
    records: list[dict[str, Any]] = []
    for family_index, (category, code, brand, capacities, ports, scenarios, alias) in enumerate(families):
        for profile_index, (compatibility, profile_alias) in enumerate(device_profiles):
            for tier in range(1, 7):
                capability = capacities[(tier + profile_index) % len(capacities)]
                price = round(11.9 + family_index * 12.5 + tier * 6.75 + profile_index * 1.4, 2)
                sku = f"SP-{code}-{profile_index + 1}{tier:02d}"
                records.append(
                    {
                        "sku": sku,
                        "name": f"{brand} {capability}{'W' if category not in {'audio', 'storage'} else 'GB'} {category.replace('_', ' ').title()} Gen {tier}",
                        "category": category,
                        "brand": brand,
                        "device_compatibility": compatibility,
                        "ports": list(ports),
                        "power_w": capability if category not in {"audio", "storage"} else None,
                        "price_usd": price,
                        "regions": list(regions[(profile_index + tier + family_index) % len(regions)]),
                        "usage_scenarios": [scenarios, profile_alias],
                        "key_features": f"Synthetic {alias}; tier {tier}; designed for {compatibility}.",
                        "limitations": "Synthetic demonstration record. Check a verified merchant source before purchase.",
                        "warranty_months": 12 if tier < 5 else 24,
                        "search_aliases": f"{alias} {compatibility} {scenarios} {profile_alias}",
                        "stock": "simulated_available" if tier != 6 else "simulated_low",
                        "source": "generated_synthetic_merchant_catalog_v1",
                        "catalog_version": "synthetic-2026.10-v1",
                    }
                )
    return records
