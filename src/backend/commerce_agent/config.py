"""Explicit server-only local configuration; never load frontend credentials."""
from pathlib import Path
import os


def load_local_config(path: Path | None = None) -> None:
    path = path or Path(__file__).parents[1] / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key.startswith("COMMERCE_") and key.replace("_", "").isalnum():
            os.environ.setdefault(key, value.strip("\"'"))
