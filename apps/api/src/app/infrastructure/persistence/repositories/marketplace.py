"""Marketplace persistence repositories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.marketplace import (
    MarketplaceApiLogModel,
    MarketplaceConnectionModel,
    MarketplaceCredentialModel,
    MarketplaceOAuthStateModel,
    MarketplaceOAuthTokenModel,
    MarketplaceSyncHistoryModel,
    MarketplaceTokenRefreshHistoryModel,
    MarketplaceWebhookEventModel,
)


class MarketplaceConnectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: MarketplaceConnectionModel) -> MarketplaceConnectionModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get(self, connection_id: uuid.UUID) -> MarketplaceConnectionModel | None:
        stmt = select(MarketplaceConnectionModel).where(
            MarketplaceConnectionModel.id == connection_id,
            MarketplaceConnectionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_workspace(
        self, workspace_id: uuid.UUID, connection_id: uuid.UUID
    ) -> MarketplaceConnectionModel | None:
        stmt = select(MarketplaceConnectionModel).where(
            MarketplaceConnectionModel.id == connection_id,
            MarketplaceConnectionModel.workspace_id == workspace_id,
            MarketplaceConnectionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_workspace(
        self, workspace_id: uuid.UUID, *, channel: str | None = None
    ) -> list[MarketplaceConnectionModel]:
        stmt = select(MarketplaceConnectionModel).where(
            MarketplaceConnectionModel.workspace_id == workspace_id,
            MarketplaceConnectionModel.deleted_at.is_(None),
        )
        if channel:
            stmt = stmt.where(MarketplaceConnectionModel.channel == channel)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_external(
        self, workspace_id: uuid.UUID, channel: str, external_account_id: str
    ) -> MarketplaceConnectionModel | None:
        stmt = select(MarketplaceConnectionModel).where(
            MarketplaceConnectionModel.workspace_id == workspace_id,
            MarketplaceConnectionModel.channel == channel,
            MarketplaceConnectionModel.external_account_id == external_account_id,
            MarketplaceConnectionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default(
        self, workspace_id: uuid.UUID, channel: str
    ) -> MarketplaceConnectionModel | None:
        stmt = select(MarketplaceConnectionModel).where(
            MarketplaceConnectionModel.workspace_id == workspace_id,
            MarketplaceConnectionModel.channel == channel,
            MarketplaceConnectionModel.is_default.is_(True),
            MarketplaceConnectionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def clear_default(self, workspace_id: uuid.UUID, channel: str) -> None:
        rows = await self.list_for_workspace(workspace_id, channel=channel)
        for row in rows:
            if row.is_default:
                row.is_default = False
        await self.session.flush()


class MarketplaceTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: MarketplaceOAuthTokenModel) -> MarketplaceOAuthTokenModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_current(self, connection_id: uuid.UUID) -> MarketplaceOAuthTokenModel | None:
        stmt = select(MarketplaceOAuthTokenModel).where(
            MarketplaceOAuthTokenModel.connection_id == connection_id,
            MarketplaceOAuthTokenModel.is_current.is_(True),
            MarketplaceOAuthTokenModel.revoked_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_all_not_current(self, connection_id: uuid.UUID) -> None:
        await self.session.execute(
            update(MarketplaceOAuthTokenModel)
            .where(MarketplaceOAuthTokenModel.connection_id == connection_id)
            .values(is_current=False)
        )
        await self.session.flush()

    async def revoke_current(self, connection_id: uuid.UUID) -> None:
        token = await self.get_current(connection_id)
        if token:
            token.revoked_at = datetime.now(UTC)
            token.is_current = False
            await self.session.flush()


class MarketplaceCredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: MarketplaceCredentialModel) -> MarketplaceCredentialModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_active(
        self, workspace_id: uuid.UUID, channel: str, environment: str
    ) -> MarketplaceCredentialModel | None:
        stmt = select(MarketplaceCredentialModel).where(
            MarketplaceCredentialModel.workspace_id == workspace_id,
            MarketplaceCredentialModel.channel == channel,
            MarketplaceCredentialModel.environment == environment,
            MarketplaceCredentialModel.is_active.is_(True),
            MarketplaceCredentialModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_workspace(self, workspace_id: uuid.UUID) -> list[MarketplaceCredentialModel]:
        stmt = select(MarketplaceCredentialModel).where(
            MarketplaceCredentialModel.workspace_id == workspace_id,
            MarketplaceCredentialModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class OAuthStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: MarketplaceOAuthStateModel) -> MarketplaceOAuthStateModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_by_state(self, state: str) -> MarketplaceOAuthStateModel | None:
        stmt = select(MarketplaceOAuthStateModel).where(MarketplaceOAuthStateModel.state == state)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class MarketplaceLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_api_log(self, row: MarketplaceApiLogModel) -> None:
        self.session.add(row)
        await self.session.flush()

    async def add_refresh_history(self, row: MarketplaceTokenRefreshHistoryModel) -> None:
        self.session.add(row)
        await self.session.flush()

    async def add_sync_history(self, row: MarketplaceSyncHistoryModel) -> None:
        self.session.add(row)
        await self.session.flush()

    async def add_webhook(self, row: MarketplaceWebhookEventModel) -> MarketplaceWebhookEventModel:
        self.session.add(row)
        await self.session.flush()
        return row
