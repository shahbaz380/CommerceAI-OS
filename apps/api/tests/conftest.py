"""Pytest fixtures for API tests including identity."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure testing env before app import side effects
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("LOG_JSON", "false")
os.environ.setdefault("OTEL_ENABLED", "false")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-characters!!")
os.environ.setdefault("DATABASE_STARTUP_VALIDATE", "false")


@pytest.fixture()
def settings(monkeypatch: pytest.MonkeyPatch):
    from app.config.settings import clear_settings_cache, get_settings

    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-with-at-least-32-characters!!")
    clear_settings_cache()
    yield get_settings()
    clear_settings_cache()


@pytest_asyncio.fixture
async def db_engine():
    from app.infrastructure.database.base import Base
    from app.infrastructure.persistence.models import identity  # noqa: F401
    from app.infrastructure.persistence.models import tenancy  # noqa: F401
    from app.infrastructure.persistence.models import marketplace  # noqa: F401

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(db_engine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    yield factory


@pytest_asyncio.fixture
async def db_session(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture()
def app(settings, db_engine, session_factory, monkeypatch):
    """App with identity DB overridden to in-memory SQLite."""
    from app.bootstrap.factory import create_app
    from app.config.settings import clear_settings_cache
    from app.core.di.container import reset_container
    from app.infrastructure.database.session import Database, reset_database_for_tests
    from app.presentation.api.deps.common import get_db_session

    clear_settings_cache()
    reset_container()
    reset_database_for_tests()

    database = Database(db_engine, session_factory, settings)

    async def _override_session():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    application = create_app(settings)

    # Prevent lifespan from connecting to real Postgres/Redis hard-fail
    monkeypatch.setenv("DATABASE_STARTUP_VALIDATE", "false")

    application.dependency_overrides[get_db_session] = _override_session

    # Patch container database after startup is tricky; override get_db too
    from app.presentation.api.deps import common as deps_common

    application.dependency_overrides[deps_common.get_db] = lambda: database

    yield application

    application.dependency_overrides.clear()
    reset_container()
    reset_database_for_tests()
    clear_settings_cache()


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client
