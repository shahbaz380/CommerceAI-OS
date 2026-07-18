"""Unit of Work port — application layer contract."""

from __future__ import annotations

import uuid
from types import TracebackType
from typing import Protocol, Self, TypeVar

from sqlalchemy.orm import DeclarativeBase

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class RepositoryPort(Protocol[ModelT]):
    async def get(self, entity_id: uuid.UUID) -> ModelT | None: ...

    async def add(self, entity: ModelT) -> ModelT: ...


class UnitOfWork(Protocol):
    """Transactional boundary for application services."""

    session: object | None
    workspace_id: uuid.UUID | None

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    def repository(
        self,
        model: type[ModelT],
        *,
        include_deleted: bool = False,
        workspace_id: uuid.UUID | None = None,
    ) -> RepositoryPort[ModelT]: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def flush(self) -> None: ...
