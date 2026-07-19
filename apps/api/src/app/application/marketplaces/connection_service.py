"""Marketplace connection application service — OAuth lifecycle orchestration."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.core.events.bus import DomainEvent, get_event_bus
from app.domain.identity.permissions import PermissionCode
from app.domain.marketplaces.enums import ConnectionStatus, MarketplaceChannel
from app.domain.marketplaces.events import (
    MARKETPLACE_CONNECTION_CONNECTED,
    MARKETPLACE_CONNECTION_DISCONNECTED,
    MARKETPLACE_CONNECTION_REAUTH_REQUIRED,
    MARKETPLACE_CONNECTION_STARTED,
    MARKETPLACE_TOKEN_REFRESHED,
)
from app.domain.marketplaces.exceptions import MarketplacePermissionDenied
from app.domain.tenancy.enums import WorkspaceRole
from app.infrastructure.marketplace.base import MarketplaceContext
from app.infrastructure.marketplace.ebay.adapter import EbayMarketplaceAdapter
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

    def _require_perm(self, principal: Principal, *codes: str) -> None:
        if principal.is_superuser:
            return
        # accept either granular marketplace_connections:* or legacy marketplace.connect
        legacy_ok = {
            PermissionCode.MARKETPLACE_CONNECTIONS_CREATE.value: PermissionCode.MARKETPLACE_CONNECT.value,
            PermissionCode.MARKETPLACE_CONNECTIONS_UPDATE.value: PermissionCode.MARKETPLACE_CONNECT.value,
            PermissionCode.MARKETPLACE_CONNECTIONS_DELETE.value: PermissionCode.MARKETPLACE_CONNECT.value,
            PermissionCode.MARKETPLACE_CONNECTIONS_REFRESH.value: PermissionCode.MARKETPLACE_CONNECT.value,
            PermissionCode.MARKETPLACE_CONNECTIONS_VALIDATE.value: PermissionCode.MARKETPLACE_CONNECT.value,
            PermissionCode.MARKETPLACE_CONNECTIONS_READ.value: PermissionCode.MARKETPLACE_CONNECT.value,
        }
        for code in codes:
            if principal.has_permission(code):
                return
            legacy = legacy_ok.get(code)
            if legacy and principal.has_permission(legacy):
                return
            # role fallback for owners/managers via workspace role checks elsewhere
        # If no granular perms seeded yet, allow when user has marketplace.connect
        if principal.has_permission(PermissionCode.MARKETPLACE_CONNECT.value):
            return
        # organization_owner / manager often have connect from seed
        if any(r in principal.roles for r in ("organization_owner", "manager", "super_admin")):
            return
        raise MarketplacePermissionDenied(f"Missing permission: {', '.join(codes)}")

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
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_READ.value)
        await self.access.require_workspace_member(principal, workspace_id)
        return await self.connections.list_for_workspace(workspace_id, channel=channel)

    async def get_connection(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ):
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_READ.value)
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
        alias: str | None = None,
        connection_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_CREATE.value)
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        if channel not in {c.value for c in MarketplaceChannel}:
            raise ValidationAppError(
                "Unknown channel", details=[{"field": "channel", "issue": channel}]
            )
        adapter = self.factory.create(channel)
        ctx = self._ctx(principal, workspace_id, environment=environment)
        result = await adapter.begin_connect(
            ctx,
            environment=environment,
            display_name=display_name,
            alias=alias,
            connection_id=connection_id,
        )
        await self.events.publish(
            DomainEvent(
                name=MARKETPLACE_CONNECTION_STARTED,
                workspace_id=str(workspace_id),
                payload={
                    "connection_id": str(result.connection_id),
                    "channel": channel,
                    "environment": environment,
                    "reconnect": bool(connection_id),
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
        oauth_error: str | None = None,
        oauth_error_description: str | None = None,
    ) -> dict[str, Any]:
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_CREATE.value)
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        if oauth_error:
            from app.domain.marketplaces.exceptions import AuthorizationFailed

            raise AuthorizationFailed(
                oauth_error_description or oauth_error or "Authorization denied by provider"
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
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_DELETE.value)
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

    async def reconnect(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        connection_id: uuid.UUID,
        *,
        environment: str | None = None,
    ) -> dict[str, Any]:
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_UPDATE.value)
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        conn = await self.get_connection(principal, workspace_id, connection_id)
        return await self.begin_connect(
            principal,
            workspace_id,
            channel=conn.channel,
            environment=environment or conn.environment,
            display_name=conn.display_name,
            alias=conn.alias,
            connection_id=connection_id,
        )

    async def refresh(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        connection_id: uuid.UUID,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_REFRESH.value)
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        conn = await self.get_connection(principal, workspace_id, connection_id)
        adapter = self.factory.create(conn.channel)
        # force: clear expires to ensure refresh path runs
        if force and isinstance(adapter, EbayMarketplaceAdapter):
            token = await adapter.tokens.get_current(connection_id)
            if token and token.expires_at:
                from datetime import UTC, datetime, timedelta

                token.expires_at = datetime.now(UTC) - timedelta(seconds=1)
                await self.session.flush()
        result = await adapter.refresh_token(self._ctx(principal, workspace_id), connection_id)
        if result.get("status") == "refreshed":
            await self.events.publish(
                DomainEvent(
                    name=MARKETPLACE_TOKEN_REFRESHED,
                    workspace_id=str(workspace_id),
                    payload={"connection_id": str(connection_id), "channel": conn.channel},
                )
            )
        # surface reauth event
        refreshed_conn = await self.connections.get_for_workspace(workspace_id, connection_id)
        if refreshed_conn and refreshed_conn.status == ConnectionStatus.REAUTH_REQUIRED:
            await self.events.publish(
                DomainEvent(
                    name=MARKETPLACE_CONNECTION_REAUTH_REQUIRED,
                    workspace_id=str(workspace_id),
                    payload={"connection_id": str(connection_id)},
                )
            )
        await self.session.flush()
        return result

    async def validate(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ) -> dict[str, Any]:
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_VALIDATE.value)
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
            "is_default": conn.is_default,
            "alias": conn.alias,
            "region": conn.region,
            "external_username": conn.external_username,
            "last_success_at": conn.last_success_at.isoformat() if conn.last_success_at else None,
            "last_refreshed_at": conn.last_refreshed_at.isoformat()
            if conn.last_refreshed_at
            else None,
            "last_validated_at": conn.last_validated_at.isoformat()
            if conn.last_validated_at
            else None,
            "last_error_code": conn.last_error_code,
            "validation": validation,
            "healthy": conn.status == ConnectionStatus.CONNECTED
            and validation.get("valid") is True,
        }

    async def set_default(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ):
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_UPDATE.value)
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        conn = await self.get_connection(principal, workspace_id, connection_id)
        adapter = self.factory.create(conn.channel)
        if not hasattr(adapter, "set_default"):
            raise ValidationAppError("set_default not supported for channel")
        return await adapter.set_default(self._ctx(principal, workspace_id), connection_id)

    async def suspend(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ):
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_UPDATE.value)
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        conn = await self.get_connection(principal, workspace_id, connection_id)
        adapter = self.factory.create(conn.channel)
        if not hasattr(adapter, "suspend"):
            raise ValidationAppError("suspend not supported for channel")
        return await adapter.suspend(self._ctx(principal, workspace_id), connection_id)

    async def resume(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ):
        self._require_perm(principal, PermissionCode.MARKETPLACE_CONNECTIONS_UPDATE.value)
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        conn = await self.get_connection(principal, workspace_id, connection_id)
        adapter = self.factory.create(conn.channel)
        if not hasattr(adapter, "resume"):
            raise ValidationAppError("resume not supported for channel")
        return await adapter.resume(self._ctx(principal, workspace_id), connection_id)

    async def ensure_fresh_access_token(
        self, principal: Principal, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ) -> dict[str, Any]:
        """Validate and refresh if access token expired/expiring — for future API callers."""
        validation = await self.validate(principal, workspace_id, connection_id)
        if validation.get("token_expired") or validation.get("token_expiring_soon"):
            if validation.get("refresh_expired"):
                return {**validation, "refresh_attempted": False, "needs_reauth": True}
            refreshed = await self.refresh(principal, workspace_id, connection_id)
            return {**validation, "refresh_attempted": True, "refresh_result": refreshed}
        return {**validation, "refresh_attempted": False}
