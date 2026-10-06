"""Environment-configured synthetic authentication and role checks."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


class AuthenticationError(ValueError):
    pass


@dataclass(frozen=True)
class Principal:
    subject: str
    role: str
    merchants: tuple[str, ...] = ()


class SyntheticAuthenticator:
    """Never stores tokens or contacts an identity provider.

    `COMMERCE_DEMO_TOKENS` is a JSON map of synthetic token to `{subject, role}`.
    Authentication is deliberately disabled unless `COMMERCE_AUTH_REQUIRED=true`.
    """

    _roles = {"viewer": 0, "support": 1, "operator": 2}

    def __init__(self, required: bool | None = None, tokens: dict | None = None) -> None:
        self.required = required if required is not None else os.getenv("COMMERCE_AUTH_REQUIRED", "false").lower() == "true"
        raw_tokens = tokens if tokens is not None else self._tokens_from_environment()
        self.tokens = raw_tokens
        if self.required and not self.tokens:
            raise RuntimeError("COMMERCE_DEMO_TOKENS must define synthetic tokens when authentication is required")

    @staticmethod
    def _tokens_from_environment() -> dict:
        raw = os.getenv("COMMERCE_DEMO_TOKENS", "{}")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("COMMERCE_DEMO_TOKENS must be valid JSON") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("COMMERCE_DEMO_TOKENS must be a JSON object")
        return parsed

    def authenticate(self, authorization: str | None) -> Principal:
        if not self.required:
            return Principal("local-development", "operator")
        if not authorization or not authorization.startswith("Bearer "):
            raise AuthenticationError("Bearer token is required")
        record = self.tokens.get(authorization[7:])
        if not isinstance(record, dict):
            raise AuthenticationError("synthetic token is invalid")
        subject, role = record.get("subject"), record.get("role")
        if not isinstance(subject, str) or role not in self._roles:
            raise AuthenticationError("synthetic token record is invalid")
        merchants = record.get("merchant_ids", [])
        if not isinstance(merchants, list) or any(not isinstance(value, str) for value in merchants):
            raise AuthenticationError("synthetic merchant scopes are invalid")
        return Principal(subject, role, tuple(merchants))

    def authorize_merchant(self, principal: Principal, merchant_id: str) -> None:
        if self.required and merchant_id not in principal.merchants:
            raise PermissionError("synthetic token is not scoped to this merchant")

    def authorize(self, principal: Principal, required_role: str) -> None:
        if self._roles[principal.role] < self._roles[required_role]:
            raise PermissionError(f"{required_role} role is required")
