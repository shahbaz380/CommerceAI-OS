"""Marketplace developer credential management."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.identity.authorization import Principal
from app.application.tenancy.tenant_access import TenantAccessService
from app.domain.marketplaces.enums import MarketplaceChannel, MarketplaceEnvironment
from app.domain.tenancy.enums import WorkspaceRole
from app.infrastructure.persistence.models.marketplace import MarketplaceCredentialModel
from app.infrastructure.persistence.repositories.marketplace import MarketplaceCredentialRepository
from app.shared.exceptions import NotFoundError, ValidationAppError


class MarketplaceCredentialService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.credentials = MarketplaceCredentialRepository(session)
        self.access = TenantAccessService(session)

    async def upsert(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        *,
        channel: str,
        environment: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: str | None = None,
        ru_name: str | None = None,
        label: str | None = None,
    ) -> MarketplaceCredentialModel:
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.OWNER
        )
        if channel not in {c.value for c in MarketplaceChannel}:
            raise ValidationAppError("Invalid channel", details=[{"field": "channel", "issue": "unknown"}])
        if environment not in {e.value for e in MarketplaceEnvironment}:
            raise ValidationAppError(
                "Invalid environment", details=[{"field": "environment", "issue": "unknown"}]
            )
        if not client_id.strip() or not client_secret.strip() or not redirect_uri.strip():
            raise ValidationAppError("client_id, client_secret, redirect_uri are required")

        existing = await self.credentials.get_active(workspace_id, channel, environment)
        if existing:
            existing.client_id = client_id.strip()
            existing.client_secret_encrypted = client_secret
            existing.redirect_uri = redirect_uri.strip()
            existing.scopes = scopes
            existing.ru_name = ru_name
            existing.label = label
            existing.is_active = True
            await self.session.flush()
            return existing

        row = MarketplaceCredentialModel(
            workspace_id=workspace_id,
            channel=channel,
            environment=environment,
            client_id=client_id.strip(),
            client_secret_encrypted=client_secret,
            redirect_uri=redirect_uri.strip(),
            scopes=scopes,
            ru_name=ru_name,
            label=label,
            is_active=True,
        )
        return await self.credentials.add(row)

    async def list(self, principal: Principal, workspace_id: uuid.UUID) -> list[MarketplaceCredentialModel]:
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        return await self.credentials.list_for_workspace(workspace_id)

    async def get(
        self, principal: Principal, workspace_id: uuid.UUID, credential_id: uuid.UUID
    ) -> MarketplaceCredentialModel:
        await self.access.require_workspace_member(
            principal, workspace_id, min_role=WorkspaceRole.MANAGER
        )
        rows = await self.credentials.list_for_workspace(workspace_id)
        for r in rows:
            if r.id == credential_id:
                return r
        raise NotFoundError("Credentials not found", code="CREDENTIALS_NOT_FOUND")
