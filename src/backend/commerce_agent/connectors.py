"""Read-only merchant connector boundary; no live connector is enabled by default."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class MerchantConnectorError(RuntimeError):
    pass


class MerchantReadConnector(Protocol):
    def readiness(self) -> dict[str, str]: ...
    def sync_catalogue(self, tenant_id: str) -> dict[str, str]: ...
    def sync_orders(self, tenant_id: str) -> dict[str, str]: ...


@dataclass
class DisabledShopifyConnector:
    """Production-shaped boundary that deliberately refuses unauthorised access."""

    reason: str = "Shopify connector is disabled until OAuth installation, sandbox approval, and encrypted token storage are configured"

    def readiness(self) -> dict[str, str]:
        return {"status": "disabled", "reason": self.reason}

    def sync_catalogue(self, tenant_id: str) -> dict[str, str]:
        raise MerchantConnectorError(self.reason)

    def sync_orders(self, tenant_id: str) -> dict[str, str]:
        raise MerchantConnectorError(self.reason)
