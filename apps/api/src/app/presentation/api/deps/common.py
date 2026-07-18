"""Common FastAPI dependencies (DI bridge)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings, get_settings
from app.core.di.container import AppContainer, get_container
from app.core.events.bus import EventBus
from app.infrastructure.cache.redis_client import RedisClient
from app.infrastructure.database.session import Database
from app.infrastructure.database.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from app.shared.types.context import RequestContext


def get_app_settings() -> AppSettings:
    return get_settings()


def get_app_container() -> AppContainer:
    return get_container()


def get_db() -> Database:
    return get_container().database


def get_redis() -> RedisClient:
    return get_container().redis


def get_events() -> EventBus:
    return get_container().event_bus


def get_request_context(request: Request) -> RequestContext:
    ctx = getattr(request.state, "request_context", None)
    if ctx is None:
        # Middleware should always set this; provide safe fallback for tests.
        from app.shared.utils.ids import new_request_id

        rid = new_request_id()
        return RequestContext(request_id=rid, correlation_id=rid)
    return ctx


async def get_db_session(
    database: Database = Depends(get_db),
) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async session (prefer get_uow for transactional use cases)."""
    session = database.session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_uow(
    request: Request,
    database: Database = Depends(get_db),
) -> AsyncIterator[SqlAlchemyUnitOfWork]:
    """Request-scoped Unit of Work with optional tenant from request context."""
    ctx = get_request_context(request)
    workspace_id = ctx.tenant.workspace_id
    uow = SqlAlchemyUnitOfWork(database.session_factory, workspace_id=workspace_id)
    async with uow:
        yield uow
