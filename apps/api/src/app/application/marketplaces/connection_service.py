"""Marketplace connection application service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.core.events.bus import DomainEvent, get_event_bus
from app.domain.marketplaces.enums import ConnectionStatus, MarketplaceChannel
from app.domain.marketplaces.events import (
    MARKETPLACE_CONNECTION_CONNECTED,
    MARKETPLACE_CONNECTION_DISCONNECTED,
    MARKETPLACE_CONNECTION_STARTED,
)
from app.domain.tenancy.enums import WorkspaceRole
from app.infrastructure.marketplace.base import MarketplaceContext
from app.infrastructure.marketplace.factory import MarketplaceFactory
from app.infrastructure.persistence.repositories.marketplace import MarketplaceConnectionRepository
from app.shared.exceptions import NotFoundError, ValidationAppError


class MarketplaceConnectionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.connections = MarketplaceConnectionRepository(session)
        self.access = TenantAccessService(session)
        self.factory = MarketplaceFactory(session)
        self.events = get_event_bus()

    def _ctx(
        self, principal: Principal, workspace_id: uuid.UUID, **kwargs: Any
    ) -> MarketplaceContext:
        return MarketplaceContext(
            workspace_id=workspace_id,
            user_id=principal.user_id,
            environment=kwargs.get("environment", "sandbox"),
            connection_id=kwargs.get("connection_id"),
        )

    async def list_channels(self) -> list[dict[str, Any]]:
        registry = self.factory.build_registry()
        out = []
        for channel, adapter in registry.all().items():
            health = await adapter.health()
            out.append({"channel": channel, **health})
        return out

    async def list_connections(
        self, principal: Principal, workspace_id: uuid.UUID, *, channel: str | None = None
    ) -> list:
        await self.access.require_workspace_member(principal, workspace_id)
        return await self.connections.list_for_workspace(workspace_id, channel=channel)

    async def get_connection(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ):
        await self.access.require_workspace_member(principal, workspace_id)
        conn = await self.connections.get_for_workspace(workspace_id, connection_id)
        if conn is None:
            raise NotFoundError("Connection not found", code="CONNECTION_NOT_FOUND")
        return conn

    async def begin_connect(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        channel: str,
        environment: str = "sandbox",
        display_name: str | None = None,
    ) -> dict[str, Any]:
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        if channel not in {c.value for c in MarketplaceChannel}:
            raise ValidationAppError("Unknown channel", details=[{"field": "channel", "issue": channel}])
        adapter = self.factory.create(channel)
        ctx = self._ctx(principal, workspace_id, environment=environment)
        result = await adapter.begin_connect(ctx, environment=environment, display_name=display_name)
        await self.events.publish(
            DomainEvent(
                name=MARKETPLACE_CONNECTION_STARTED,
                workspace_id=str(workspace_id),
                payload={
                    "connection_id": str(result.connection_id),
                    "channel": channel,
                    "environment": environment,
                },
            )
        )
        await self.session.flush()
        return {
            "connection_id": result.connection_id,
            "status": result.status,
            "authorization_url": result.authorization_url,
            "state": result.state,
            "channel": channel,
            "environment": environment,
        }

    async def complete_connect(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        channel: str,
        code: str,
        state: str,
        connection_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        adapter = self.factory.create(channel)
        ctx = self._ctx(principal, workspace_id)
        result = await adapter.complete_connect(
            ctx, code=code, state=state, connection_id=connection_id
        )
        await self.events.publish(
            DomainEvent(
                name=MARKETPLACE_CONNECTION_CONNECTED,
                workspace_id=str(workspace_id),
                payload={
                    "connection_id": str(result.connection_id),
                    "channel": channel,
                    "status": result.status,
                },
            )
        )
        await self.session.flush()
        return {
            "connection_id": result.connection_id,
            "status": result.status,
            "external_account_id": result.external_account_id,
            "display_name": result.display_name,
        }

    async def disconnect(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ) -> None:
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        conn = await self.get_connection(principal, workspace_id, connection_id)
        adapter = self.factory.create(conn.channel)
        await adapter.disconnect(self._ctx(principal, workspace_id), connection_id)
        await self.events.publish(
            DomainEvent(
                name=MARKETPLACE_CONNECTION_DISCONNECTED,
                workspace_id=str(workspace_id),
                payload={"connection_id": str(connection_id), "channel": conn.channel},
            )
        )
        await self.session.flush()

    async def refresh(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ) -> dict[str, Any]:
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        conn = await self.get_connection(principal, workspace_id, connection_id)
        adapter = self.factory.create(conn.channel)
        return await adapter.refresh_token(self._ctx(principal, workspace_id), connection_id)

    async def validate(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ) -> dict[str, Any]:
        await self.access.require_workspace_member(principal, workspace_id)
        conn = await self.get_connection(principal, workspace_id, connection_id)
        adapter = self.factory.create(conn.channel)
        return await adapter.validate_connection(self._ctx(principal, workspace_id), connection_id)

    async def health(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ) -> dict[str, Any]:
        conn = await self.get_connection(principal, workspace_id, connection_id)
        validation = await self.validate(principal, workspace_id, connection_id)
        return {
            "connection_id": str(conn.id),
            "channel": conn.channel,
            "status": conn.status,
            "environment": conn.environment,
            "last_success_at": conn.last_success_at.isoformat() if conn.last_success_at else None,
            "last_error_code": conn.last_error_code,
            "validation": validation,
            "healthy": conn.status == ConnectionStatus.CONNECTED and validation.get("valid") is True,
        }
