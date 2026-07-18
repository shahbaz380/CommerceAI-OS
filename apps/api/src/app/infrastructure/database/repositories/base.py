"""Generic async repository base (Repository Pattern).

Works with any SQLAlchemy mapped class. Soft-delete and tenancy are optional
based on model attributes.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.infrastructure.database.repositories.specification import (
    NotDeletedSpec,
    Specification,
    TenantIdSpec,
    TrueSpec,
)
from app.shared.exceptions import ConflictError, NotFoundError

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class SqlAlchemyRepository(Generic[ModelT]):
    """Async generic repository for a single aggregate/table model."""

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelT],
        *,
        workspace_id: uuid.UUID | None = None,
        include_deleted: bool = False,
    ) -> None:
        self.session = session
        self.model = model
        self.workspace_id = workspace_id
        self.include_deleted = include_deleted

    # --- query building -------------------------------------------------

    def _base_select(self) -> Select[tuple[ModelT]]:
        stmt: Select[tuple[ModelT]] = select(self.model)
        spec: Specification[ModelT] = TrueSpec()
        if not self.include_deleted and hasattr(self.model, "deleted_at"):
            spec = spec & NotDeletedSpec()
        if self.workspace_id is not None and hasattr(self.model, "workspace_id"):
            spec = spec & TenantIdSpec(self.workspace_id)
        return spec.apply(stmt, self.model)

    # --- reads ----------------------------------------------------------

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        stmt = self._base_select().where(self.model.id == entity_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_raise(self, entity_id: uuid.UUID) -> ModelT:
        entity = await self.get(entity_id)
        if entity is None:
            raise NotFoundError(
                f"{self.model.__name__} not found",
                code="ENTITY_NOT_FOUND",
                details=[{"field": "id", "issue": str(entity_id)}],
            )
        return entity

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        specification: Specification[ModelT] | None = None,
    ) -> Sequence[ModelT]:
        limit = max(1, min(limit, 500))
        offset = max(0, offset)
        stmt = self._base_select()
        if specification is not None:
            stmt = specification.apply(stmt, self.model)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, specification: Specification[ModelT] | None = None) -> int:
        # Count with same filters as list
        stmt = self._base_select()
        if specification is not None:
            stmt = specification.apply(stmt, self.model)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return int(result.scalar_one())

    async def exists(self, entity_id: uuid.UUID) -> bool:
        return await self.get(entity_id) is not None

    # --- writes ---------------------------------------------------------

    async def add(self, entity: ModelT) -> ModelT:
        if (
            self.workspace_id is not None
            and hasattr(entity, "workspace_id")
            and getattr(entity, "workspace_id", None) is None
        ):
            setattr(entity, "workspace_id", self.workspace_id)
        if (
            self.workspace_id is not None
            and hasattr(entity, "workspace_id")
            and getattr(entity, "workspace_id") != self.workspace_id
        ):
            raise ConflictError(
                "Entity workspace_id does not match repository tenant scope",
                code="TENANT_MISMATCH",
            )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def add_many(self, entities: Sequence[ModelT]) -> Sequence[ModelT]:
        for entity in entities:
            await self.add(entity)
        return entities

    async def delete(self, entity: ModelT, *, hard: bool = False) -> None:
        if not hard and hasattr(entity, "soft_delete"):
            entity.soft_delete()  # type: ignore[attr-defined]
            await self.session.flush()
            return
        await self.session.delete(entity)
        await self.session.flush()

    async def delete_by_id(self, entity_id: uuid.UUID, *, hard: bool = False) -> None:
        entity = await self.get_or_raise(entity_id)
        await self.delete(entity, hard=hard)

    async def restore(self, entity_id: uuid.UUID) -> ModelT:
        # Need to include deleted rows
        prev = self.include_deleted
        self.include_deleted = True
        try:
            entity = await self.get_or_raise(entity_id)
            if hasattr(entity, "restore"):
                entity.restore()  # type: ignore[attr-defined]
            await self.session.flush()
            return entity
        finally:
            self.include_deleted = prev


# Alias for documentation / imports
GenericRepository = SqlAlchemyRepository
