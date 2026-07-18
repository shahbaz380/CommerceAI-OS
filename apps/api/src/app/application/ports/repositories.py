"""Repository port protocols (optional typing for application services)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Protocol, TypeVar

from sqlalchemy.orm import DeclarativeBase

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class AsyncRepository(Protocol[ModelT]):
    async def get(self, entity_id: uuid.UUID) -> ModelT | None: ...

    async def get_or_raise(self, entity_id: uuid.UUID) -> ModelT: ...

    async def list(self, *, offset: int = 0, limit: int = 50) -> Sequence[ModelT]: ...

    async def count(self) -> int: ...

    async def add(self, entity: ModelT) -> ModelT: ...

    async def delete(self, entity: ModelT, *, hard: bool = False) -> None: ...
