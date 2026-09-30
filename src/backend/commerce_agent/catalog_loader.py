"""Load reviewed synthetic catalogue and policy assets migrated from Dify."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).with_name("data")


def _parts(value: str, separators: tuple[str, ...] = ("|", "+")) -> list[str]:
    normalized = value or ""
    for separator in separators:
        normalized = normalized.replace(separator, "|")
    return [item.strip() for item in normalized.split("|") if item.strip()]


def _number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_dify_products() -> list[dict[str, Any]]:
    """Return only synthetic products packaged with this repository."""
    path = DATA_DIR / "dify_product_catalog.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            {
                "sku": row["sku_id"].strip(), "name": row["product_name"].strip(),
                "category": row["category"].strip().lower(), "brand": row["brand"].strip(),
                "device_compatibility": row["device_compatibility"].strip(),
                "ports": _parts(row["connector"]), "power_w": _number(row["power_watt"]),
                "price_usd": _number(row["price_usd"]), "regions": _parts(row["country_available"]),
                "usage_scenarios": _parts(row["usage_scenario"], ("|", ",", ";")),
                "key_features": row["key_features"].strip(), "limitations": row["limitations"].strip(),
                "warranty_months": _number(row["warranty_months"]), "search_aliases": row["search_aliases"].strip(),
                "stock": "simulated_available", "source": "dify_synthetic_catalog_migration",
            }
            for row in csv.DictReader(handle)
        ]


def load_dify_policies() -> list[dict[str, Any]]:
    """Return only synthetic policy records packaged with this repository."""
    path = DATA_DIR / "dify_policy_catalog.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            {
                "policy_id": row["policy_id"].strip(), "topic": row["topic"].strip().lower(),
                "policy_type": row["policy_type"].strip().lower(), "region": row["region"].strip().upper(),
                "question": row["question"].strip(), "summary": row["standard_answer"].strip(),
                "keywords": _parts(row["keywords"], ("|", ",", ";")), "priority": row["priority"].strip(),
                "risk_level": row["risk_level"].strip(), "effective_from": row["last_updated"].strip(),
                "source": "dify_synthetic_policy_migration",
            }
            for row in csv.DictReader(handle)
        ]
