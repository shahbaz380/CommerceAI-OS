"""Domain models for marketplace providers and accounts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.common.entity import Entity
from app.domain.marketplaces.enums import MarketplaceEnvironment, MarketplaceProvider, MarketplaceStatus


@dataclass(slots=True, frozen=True)
class MarketplaceCapability:
    """Describes a capability supported by a provider adapter."""

    name: str
    supported: bool = True
    description: str = ""


@dataclass(slots=True, frozen=True)
class MarketplaceProviderDefinition:
    """Provider metadata used by the provider resolver and registration services."""

    provider: MarketplaceProvider
    channel: str
    display_name: str
    capabilities: tuple[MarketplaceCapability, ...] = field(default_factory=tuple)
    default_environment: MarketplaceEnvironment = MarketplaceEnvironment.SANDBOX


@dataclass(slots=True, kw_only=True)
class Marketplace(Entity):
    """Marketplace catalog entry for supported providers."""

    provider: MarketplaceProvider
    channel: str
    display_name: str
    status: MarketplaceStatus = MarketplaceStatus.ACTIVE
    capabilities: tuple[MarketplaceCapability, ...] = field(default_factory=tuple)
    description: str | None = None
    supports_oauth: bool = True
    supports_inventory: bool = False
    supports_orders: bool = False
    supports_messages: bool = False
    default_environment: MarketplaceEnvironment = MarketplaceEnvironment.SANDBOX
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class MarketplaceAccount(Entity):
    """Workspace-level marketplace account abstraction."""

    workspace_id: UUID
    provider: MarketplaceProvider
    channel: str
    status: MarketplaceStatus = MarketplaceStatus.PENDING
    external_account_id: str | None = None
    display_name: str | None = None
    environment: MarketplaceEnvironment = MarketplaceEnvironment.SANDBOX
    is_default: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    connected_at: datetime | None = None
    disconnected_at: datetime | None = None
    last_validated_at: datetime | None = None

    def activate(self) -> None:
        self.status = MarketplaceStatus.ACTIVE
        self.connected_at = self.connected_at or datetime.now(UTC)
        self.disconnected_at = None

    def deactivate(self) -> None:
        self.status = MarketplaceStatus.INACTIVE
        self.disconnected_at = datetime.now(UTC)

    def mark_error(self, reason: str) -> None:
        self.status = MarketplaceStatus.ERROR
        self.metadata["last_error"] = reason


__all__ = [
    "Marketplace",
    "MarketplaceAccount",
    "MarketplaceCapability",
    "MarketplaceProviderDefinition",
]
