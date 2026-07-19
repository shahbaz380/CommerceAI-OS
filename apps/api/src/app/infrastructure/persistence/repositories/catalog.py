"""Catalog repositories."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.catalog import (
    ProductAttributeDefinitionModel,
    ProductAttributeValueModel,
    ProductCategoryAssignmentModel,
    ProductCategoryModel,
    ProductIdentifierModel,
    ProductMediaModel,
    ProductModel,
    ProductVariantModel,
)


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, product: ProductModel) -> ProductModel:
        self.session.add(product)
        await self.session.flush()
        return product

    async def get(self, workspace_id: uuid.UUID, product_id: uuid.UUID) -> ProductModel | None:
        stmt = select(ProductModel).where(
            ProductModel.id == product_id,
            ProductModel.workspace_id == workspace_id,
            ProductModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(self, workspace_id: uuid.UUID, sku: str) -> ProductModel | None:
        stmt = select(ProductModel).where(
            ProductModel.workspace_id == workspace_id,
            ProductModel.default_sku == sku,
            ProductModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _search_stmt(
        self,
        workspace_id: uuid.UUID,
        *,
        status: str | None = None,
        brand: str | None = None,
        product_type: str | None = None,
        sku: str | None = None,
        q: str | None = None,
        category_id: uuid.UUID | None = None,
    ) -> Select[tuple[ProductModel]]:
        stmt = select(ProductModel).where(
            ProductModel.workspace_id == workspace_id,
            ProductModel.deleted_at.is_(None),
        )
        if status:
            stmt = stmt.where(ProductModel.status == status)
        if brand:
            stmt = stmt.where(ProductModel.brand.ilike(f"%{brand}%"))
        if product_type:
            stmt = stmt.where(ProductModel.product_type == product_type)
        if sku:
            stmt = stmt.where(ProductModel.default_sku == sku.upper())
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    ProductModel.name.ilike(like),
                    ProductModel.internal_title.ilike(like),
                    ProductModel.description.ilike(like),
                    ProductModel.default_sku.ilike(like),
                )
            )
        if category_id:
            stmt = stmt.join(
                ProductCategoryAssignmentModel,
                ProductCategoryAssignmentModel.product_id == ProductModel.id,
            ).where(ProductCategoryAssignmentModel.category_id == category_id)
        return stmt

    async def search(
        self,
        workspace_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
        **filters: Any,
    ) -> Sequence[ProductModel]:
        limit = max(1, min(limit, 200))
        stmt = self._search_stmt(workspace_id, **filters).order_by(ProductModel.created_at.desc())
        stmt = stmt.offset(max(0, offset)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def count(self, workspace_id: uuid.UUID, **filters: Any) -> int:
        base = self._search_stmt(workspace_id, **filters).subquery()
        result = await self.session.execute(select(func.count()).select_from(base))
        return int(result.scalar_one())


class ProductVariantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, variant: ProductVariantModel) -> ProductVariantModel:
        self.session.add(variant)
        await self.session.flush()
        return variant

    async def get(
        self, workspace_id: uuid.UUID, product_id: uuid.UUID, variant_id: uuid.UUID
    ) -> ProductVariantModel | None:
        stmt = select(ProductVariantModel).where(
            ProductVariantModel.id == variant_id,
            ProductVariantModel.product_id == product_id,
            ProductVariantModel.workspace_id == workspace_id,
            ProductVariantModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(self, workspace_id: uuid.UUID, sku: str) -> ProductVariantModel | None:
        stmt = select(ProductVariantModel).where(
            ProductVariantModel.workspace_id == workspace_id,
            ProductVariantModel.sku == sku,
            ProductVariantModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_product(
        self, workspace_id: uuid.UUID, product_id: uuid.UUID
    ) -> Sequence[ProductVariantModel]:
        stmt = select(ProductVariantModel).where(
            ProductVariantModel.workspace_id == workspace_id,
            ProductVariantModel.product_id == product_id,
            ProductVariantModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ProductCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, category: ProductCategoryModel) -> ProductCategoryModel:
        self.session.add(category)
        await self.session.flush()
        return category

    async def get(self, workspace_id: uuid.UUID, category_id: uuid.UUID) -> ProductCategoryModel | None:
        stmt = select(ProductCategoryModel).where(
            ProductCategoryModel.id == category_id,
            ProductCategoryModel.workspace_id == workspace_id,
            ProductCategoryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, workspace_id: uuid.UUID, slug: str) -> ProductCategoryModel | None:
        stmt = select(ProductCategoryModel).where(
            ProductCategoryModel.workspace_id == workspace_id,
            ProductCategoryModel.slug == slug,
            ProductCategoryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, workspace_id: uuid.UUID) -> Sequence[ProductCategoryModel]:
        stmt = (
            select(ProductCategoryModel)
            .where(
                ProductCategoryModel.workspace_id == workspace_id,
                ProductCategoryModel.deleted_at.is_(None),
            )
            .order_by(ProductCategoryModel.depth, ProductCategoryModel.sort_order, ProductCategoryModel.name)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ProductMediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, media: ProductMediaModel) -> ProductMediaModel:
        self.session.add(media)
        await self.session.flush()
        return media

    async def get(
        self, workspace_id: uuid.UUID, product_id: uuid.UUID, media_id: uuid.UUID
    ) -> ProductMediaModel | None:
        stmt = select(ProductMediaModel).where(
            ProductMediaModel.id == media_id,
            ProductMediaModel.product_id == product_id,
            ProductMediaModel.workspace_id == workspace_id,
            ProductMediaModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_product(
        self, workspace_id: uuid.UUID, product_id: uuid.UUID
    ) -> Sequence[ProductMediaModel]:
        stmt = (
            select(ProductMediaModel)
            .where(
                ProductMediaModel.workspace_id == workspace_id,
                ProductMediaModel.product_id == product_id,
                ProductMediaModel.deleted_at.is_(None),
            )
            .order_by(ProductMediaModel.sort_order, ProductMediaModel.created_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def clear_primary(
        self,
        workspace_id: uuid.UUID,
        product_id: uuid.UUID,
        *,
        variant_id: uuid.UUID | None = None,
    ) -> None:
        rows = await self.list_for_product(workspace_id, product_id)
        for row in rows:
            if variant_id is None and row.variant_id is None and row.is_primary:
                row.is_primary = False
            elif variant_id is not None and row.variant_id == variant_id and row.is_primary:
                row.is_primary = False
        await self.session.flush()


class ProductIdentifierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: ProductIdentifierModel) -> ProductIdentifierModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_for_product(
        self, workspace_id: uuid.UUID, product_id: uuid.UUID
    ) -> Sequence[ProductIdentifierModel]:
        stmt = select(ProductIdentifierModel).where(
            ProductIdentifierModel.workspace_id == workspace_id,
            ProductIdentifierModel.product_id == product_id,
            ProductIdentifierModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ProductAttributeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_definition(
        self, row: ProductAttributeDefinitionModel
    ) -> ProductAttributeDefinitionModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_definition(
        self, workspace_id: uuid.UUID, definition_id: uuid.UUID
    ) -> ProductAttributeDefinitionModel | None:
        stmt = select(ProductAttributeDefinitionModel).where(
            ProductAttributeDefinitionModel.id == definition_id,
            ProductAttributeDefinitionModel.workspace_id == workspace_id,
            ProductAttributeDefinitionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_value(self, row: ProductAttributeValueModel) -> ProductAttributeValueModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_values(
        self, workspace_id: uuid.UUID, product_id: uuid.UUID
    ) -> Sequence[ProductAttributeValueModel]:
        stmt = select(ProductAttributeValueModel).where(
            ProductAttributeValueModel.workspace_id == workspace_id,
            ProductAttributeValueModel.product_id == product_id,
            ProductAttributeValueModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ProductCategoryAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, row: ProductCategoryAssignmentModel) -> ProductCategoryAssignmentModel:
        self.session.add(row)
        await self.session.flush()
        return row

    async def exists(self, product_id: uuid.UUID, category_id: uuid.UUID) -> bool:
        stmt = select(ProductCategoryAssignmentModel.id).where(
            ProductCategoryAssignmentModel.product_id == product_id,
            ProductCategoryAssignmentModel.category_id == category_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
