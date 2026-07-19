"""Listing repositories."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.listings import (
    ListingContentModel,
    ListingMarketplaceMappingModel,
    ListingModel,
    ListingStatusHistoryModel,
    ListingTemplateModel,
    ListingValidationIssueModel,
    ListingValidationResultModel,
    ListingVersionModel,
)


class ListingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, listing: ListingModel) -> ListingModel:
        self.session.add(listing)
        await self.session.flush()
        return listing

    async def get(self, workspace_id: uuid.UUID, listing_id: uuid.UUID) -> ListingModel | None:
        stmt = select(ListingModel).where(
            ListingModel.id == listing_id,
            ListingModel.workspace_id == workspace_id,
            ListingModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _search_stmt(
        self,
        workspace_id: uuid.UUID,
        *,
        status: str | None = None,
        product_id: uuid.UUID | None = None,
        marketplace_type: str | None = None,
        q: str | None = None,
    ) -> Select[tuple[ListingModel]]:
        stmt = select(ListingModel).where(
            ListingModel.workspace_id == workspace_id,
            ListingModel.deleted_at.is_(None),
        )
        if status:
            stmt = stmt.where(ListingModel.status == status)
        if product_id:
            stmt = stmt.where(ListingModel.product_id == product_id)
        if marketplace_type:
            stmt = stmt.where(ListingModel.marketplace_type == marketplace_type)
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    ListingModel.internal_title.ilike(like),
                    ListingModel.marketplace_title.ilike(like),
                    ListingModel.subtitle.ilike(like),
                )
            )
        return stmt

    async def search(
        self,
        workspace_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
        **filters: Any,
    ) -> Sequence[ListingModel]:
        limit = max(1, min(limit, 200))
        stmt = self._search_stmt(workspace_id, **filters).order_by(ListingModel.created_at.desc())
        stmt = stmt.offset(max(0, offset)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, workspace_id: uuid.UUID, **filters: Any) -> int:
        base = self._search_stmt(workspace_id, **filters).subquery()
        result = await self.session.execute(select(func.count()).select_from(base))
        return int(result.scalar_one())


class ListingContentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, content: ListingContentModel) -> ListingContentModel:
        self.session.add(content)
        await self.session.flush()
        return content

    async def get_by_listing(
        self, workspace_id: uuid.UUID, listing_id: uuid.UUID
    ) -> ListingContentModel | None:
        stmt = select(ListingContentModel).where(
            ListingContentModel.listing_id == listing_id,
            ListingContentModel.workspace_id == workspace_id,
            ListingContentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ListingTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, template: ListingTemplateModel) -> ListingTemplateModel:
        self.session.add(template)
        await self.session.flush()
        return template

    async def get(self, workspace_id: uuid.UUID, template_id: uuid.UUID) -> ListingTemplateModel | None:
        stmt = select(ListingTemplateModel).where(
            ListingTemplateModel.id == template_id,
            ListingTemplateModel.workspace_id == workspace_id,
            ListingTemplateModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, workspace_id: uuid.UUID) -> Sequence[ListingTemplateModel]:
        stmt = select(ListingTemplateModel).where(
            ListingTemplateModel.workspace_id == workspace_id,
            ListingTemplateModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ListingVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, version: ListingVersionModel) -> ListingVersionModel:
        self.session.add(version)
        await self.session.flush()
        return version

    async def next_version_number(self, listing_id: uuid.UUID) -> int:
        stmt = select(func.coalesce(func.max(ListingVersionModel.version_number), 0)).where(
            ListingVersionModel.listing_id == listing_id
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one()) + 1

    async def list_for_listing(
        self, workspace_id: uuid.UUID, listing_id: uuid.UUID
    ) -> Sequence[ListingVersionModel]:
        stmt = (
            select(ListingVersionModel)
            .where(
                ListingVersionModel.workspace_id == workspace_id,
                ListingVersionModel.listing_id == listing_id,
            )
            .order_by(ListingVersionModel.version_number.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ListingValidationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_result(self, row: ListingValidationResultModel) -> ListingValidationResultModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def add_issue(self, row: ListingValidationIssueModel) -> None:
        self.session.add(row)
        await self.session.flush()

    async def latest_for_listing(
        self, workspace_id: uuid.UUID, listing_id: uuid.UUID
    ) -> ListingValidationResultModel | None:
        stmt = (
            select(ListingValidationResultModel)
            .where(
                ListingValidationResultModel.workspace_id == workspace_id,
                ListingValidationResultModel.listing_id == listing_id,
            )
            .order_by(ListingValidationResultModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_issues(
        self, validation_result_id: uuid.UUID
    ) -> Sequence[ListingValidationIssueModel]:
        stmt = select(ListingValidationIssueModel).where(
            ListingValidationIssueModel.validation_result_id == validation_result_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ListingStatusHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: ListingStatusHistoryModel) -> None:
        self.session.add(row)
        await self.session.flush()


class ListingMappingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: ListingMarketplaceMappingModel) -> ListingMarketplaceMappingModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_for_listing(
        self, workspace_id: uuid.UUID, listing_id: uuid.UUID
    ) -> Sequence[ListingMarketplaceMappingModel]:
        stmt = select(ListingMarketplaceMappingModel).where(
            ListingMarketplaceMappingModel.workspace_id == workspace_id,
            ListingMarketplaceMappingModel.listing_id == listing_id,
            ListingMarketplaceMappingModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
