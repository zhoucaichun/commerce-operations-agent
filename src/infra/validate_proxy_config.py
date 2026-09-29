"""Pre-deployment validation for the Nginx template; never reads private keys."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


REQUIRED = ("listen 443 ssl", "ssl_certificate ", "ssl_certificate_key ", "TLSv1.2 TLSv1.3", "proxy_pass http://api:8000")


def validate(template: Path, public_host: str) -> list[str]:
    errors: list[str] = []
    text = template.read_text(encoding="utf-8")
    if not re.fullmatch(r"[A-Za-z0-9.-]+", public_host) or public_host.endswith(".invalid"):
        errors.append("COMMERCE_PUBLIC_HOST must be a non-placeholder DNS name")
    for marker in REQUIRED:
        if marker not in text:
            errors.append(f"missing required proxy directive: {marker}")
    if "ssl_protocols TLSv1.2 TLSv1.3;" not in text:
        errors.append("only TLSv1.2 and TLSv1.3 are permitted")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--template", type=Path, default=Path(__file__).parent / "nginx" / "commerce-agent.conf")
    args = parser.parse_args()
    errors = validate(args.template, args.host)
    if errors:
        raise SystemExit("proxy validation failed: " + "; ".join(errors))
    print("proxy template validation passed; next run nginx -t with operator-managed certificates")


if __name__ == "__main__":
    main()
