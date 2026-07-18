"""SQLAlchemy async Unit of Work.

Coordinates a single AsyncSession transaction and exposes repository factory.
"""

from __future__ import annotations

import uuid
from types import TracebackType
from typing import Self, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.infrastructure.database.repositories.base import SqlAlchemyRepository
from app.infrastructure.logging.setup import get_logger

logger = get_logger("app")

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class SqlAlchemyUnitOfWork:
    """Async Unit of Work — one business transaction per scope."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        workspace_id: uuid.UUID | None = None,
    ) -> None:
        self._session_factory = session_factory
        self.workspace_id = workspace_id
        self.session: AsyncSession | None = None
        self._committed = False

    async def __aenter__(self) -> Self:
        self.session = self._session_factory()
        self._committed = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
            elif not self._committed:
                # Default: rollback uncommitted work (explicit commit required)
                await self.rollback()
        finally:
            if self.session is not None:
                await self.session.close()
                self.session = None

    def get_session(self) -> AsyncSession:
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not active; use 'async with uow'")
        return self.session

    def repository(
        self,
        model: type[ModelT],
        *,
        include_deleted: bool = False,
        workspace_id: uuid.UUID | None = None,
    ) -> SqlAlchemyRepository[ModelT]:
        return SqlAlchemyRepository(
            self.get_session(),
            model,
            workspace_id=workspace_id if workspace_id is not None else self.workspace_id,
            include_deleted=include_deleted,
        )

    async def commit(self) -> None:
        session = self.get_session()
        await session.commit()
        self._committed = True
        logger.debug("uow_committed")

    async def rollback(self) -> None:
        if self.session is None:
            return
        await self.session.rollback()
        self._committed = False
        logger.debug("uow_rolled_back")

    async def flush(self) -> None:
        await self.get_session().flush()

    async def refresh(self, entity: Any) -> None:  # noqa: ANN401
        await self.get_session().refresh(entity)


# late import avoidance
from typing import Any  # noqa: E402
