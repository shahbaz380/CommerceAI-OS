"""Persistence foundation integration tests (SQLite in-memory).

Uses an infrastructure probe model (not a product business table) to validate
mixins, repository, unit of work, soft delete, and tenancy filters.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import AuditedTenantModel, Base
from app.infrastructure.database.mixins.version import VersionMixin
from app.infrastructure.database.repositories.base import SqlAlchemyRepository
from app.infrastructure.database.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork


class PersistenceProbe(AuditedTenantModel):
    """Test-only mapped class to exercise enterprise mixins.

    Not a CommerceAI business entity — exists solely for foundation tests.
    """

    __tablename__ = "persistence_probes"
    __mapper_args__ = {"version_id_col": VersionMixin.version}

    name: Mapped[str] = mapped_column(String(120), nullable=False)


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_uow_commit_and_get(session_factory: async_sessionmaker[AsyncSession]) -> None:
    workspace = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(session_factory, workspace_id=workspace) as uow:
        repo = uow.repository(PersistenceProbe)
        entity = PersistenceProbe(name="alpha", workspace_id=workspace)
        await repo.add(entity)
        entity_id = entity.id
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory, workspace_id=workspace) as uow:
        repo = uow.repository(PersistenceProbe)
        loaded = await repo.get(entity_id)
        assert loaded is not None
        assert loaded.name == "alpha"
        assert loaded.workspace_id == workspace
        assert loaded.version == 1


@pytest.mark.asyncio
async def test_soft_delete_hides_row(session_factory: async_sessionmaker[AsyncSession]) -> None:
    workspace = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(session_factory, workspace_id=workspace) as uow:
        repo = uow.repository(PersistenceProbe)
        entity = PersistenceProbe(name="beta", workspace_id=workspace)
        await repo.add(entity)
        entity_id = entity.id
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory, workspace_id=workspace) as uow:
        repo = uow.repository(PersistenceProbe)
        entity = await repo.get_or_raise(entity_id)
        await repo.delete(entity)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory, workspace_id=workspace) as uow:
        repo = uow.repository(PersistenceProbe)
        assert await repo.get(entity_id) is None
        repo_all = uow.repository(PersistenceProbe, include_deleted=True)
        deleted = await repo_all.get(entity_id)
        assert deleted is not None
        assert deleted.is_deleted


@pytest.mark.asyncio
async def test_tenant_isolation(session_factory: async_sessionmaker[AsyncSession]) -> None:
    ws_a = uuid.uuid4()
    ws_b = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await uow.repository(PersistenceProbe, workspace_id=ws_a).add(
            PersistenceProbe(name="a", workspace_id=ws_a)
        )
        await uow.repository(PersistenceProbe, workspace_id=ws_b).add(
            PersistenceProbe(name="b", workspace_id=ws_b)
        )
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory, workspace_id=ws_a) as uow:
        rows = await uow.repository(PersistenceProbe).list()
        assert len(rows) == 1
        assert rows[0].name == "a"


@pytest.mark.asyncio
async def test_uow_rollback_discards_changes(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    workspace = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(session_factory, workspace_id=workspace) as uow:
        await uow.repository(PersistenceProbe).add(
            PersistenceProbe(name="gamma", workspace_id=workspace)
        )
        await uow.rollback()

    async with SqlAlchemyUnitOfWork(session_factory, workspace_id=workspace) as uow:
        assert await uow.repository(PersistenceProbe).count() == 0


@pytest.mark.asyncio
async def test_tenant_mismatch_on_add(session_factory: async_sessionmaker[AsyncSession]) -> None:
    from app.shared.exceptions import ConflictError

    ws_a = uuid.uuid4()
    ws_b = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(session_factory, workspace_id=ws_a) as uow:
        repo = uow.repository(PersistenceProbe)
        with pytest.raises(ConflictError):
            await repo.add(PersistenceProbe(name="x", workspace_id=ws_b))


@pytest.mark.asyncio
async def test_repository_without_uow(session_factory: async_sessionmaker[AsyncSession]) -> None:
    workspace = uuid.uuid4()
    async with session_factory() as session:
        repo = SqlAlchemyRepository(session, PersistenceProbe, workspace_id=workspace)
        await repo.add(PersistenceProbe(name="direct", workspace_id=workspace))
        await session.commit()
        assert await repo.count() == 1
