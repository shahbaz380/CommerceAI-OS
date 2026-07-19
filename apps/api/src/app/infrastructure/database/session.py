"""Async SQLAlchemy engine, session factory, connection manager, pool utilities.

No business ORM models required for this module to operate.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, Pool

from app.config.settings import AppEnvironment, AppSettings, get_settings
from app.infrastructure.logging.setup import get_logger

logger = get_logger("app")


@dataclass(frozen=True, slots=True)
class PoolStats:
    """Snapshot of connection pool counters (best-effort)."""

    pool_class: str
    size: int | None = None
    checked_in: int | None = None
    checked_out: int | None = None
    overflow: int | None = None
    invalid: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "pool_class": self.pool_class,
            "size": self.size,
            "checked_in": self.checked_in,
            "checked_out": self.checked_out,
            "overflow": self.overflow,
            "invalid": self.invalid,
        }


class Database:
    """Connection manager holding engine + session factory."""

    def __init__(
        self,
        engine: AsyncEngine,
        session_factory: async_sessionmaker[AsyncSession],
        settings: AppSettings,
    ) -> None:
        self.engine = engine
        self.session_factory = session_factory
        self.settings = settings

    async def healthcheck(self) -> bool:
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.warning("database_healthcheck_failed", error=str(exc))
            return False

    async def verify_connection(self) -> dict[str, Any]:
        """Detailed connection verification for ops endpoints."""
        started_ok = False
        server_version: str | None = None
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT version()"))
                server_version = str(result.scalar_one())
                started_ok = True
        except Exception as exc:
            return {"ok": False, "error": str(exc), "pool": self.pool_stats().as_dict()}
        return {
            "ok": started_ok,
            "dialect": self.engine.dialect.name,
            "driver": self.engine.url.drivername,
            "server_version": server_version,
            "pool": self.pool_stats().as_dict(),
        }

    def pool_stats(self) -> PoolStats:
        pool = self.engine.sync_engine.pool
        pool_class = pool.__class__.__name__
        if isinstance(pool, NullPool) or not hasattr(pool, "size"):
            return PoolStats(pool_class=pool_class)
        try:
            return PoolStats(
                pool_class=pool_class,
                size=pool.size(),  # type: ignore[no-untyped-call]
                checked_in=pool.checkedin(),  # type: ignore[no-untyped-call]
                checked_out=pool.checkedout(),  # type: ignore[no-untyped-call]
                overflow=pool.overflow(),  # type: ignore[no-untyped-call]
                invalid=getattr(pool, "invalidated", lambda: None)(),
            )
        except Exception:
            return PoolStats(pool_class=pool_class)

    async def dispose(self) -> None:
        logger.info("database_engine_dispose")
        await self.engine.dispose()


_database: Database | None = None


def _build_engine(settings: AppSettings) -> AsyncEngine:
    """Create async engine with environment-appropriate pooling."""
    url = settings.database_url
    connect_args: dict[str, Any] = {}

    # SQLite (tests): use NullPool + check_same_thread
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine = create_async_engine(
            url,
            echo=settings.database_echo,
            poolclass=NullPool,
            connect_args=connect_args,
        )
        return engine

    # PostgreSQL async
    if settings.app_env == AppEnvironment.TESTING and "sqlite" not in url:
        # Prefer NullPool for highly parallel tests against shared PG
        poolclass: type[Pool] | None = NullPool
        engine = create_async_engine(
            url,
            echo=settings.database_echo,
            poolclass=poolclass,
            pool_pre_ping=True,
        )
        return engine

    engine = create_async_engine(
        url,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_pre_ping=True,
        pool_recycle=settings.database_pool_recycle,
    )

    # Optional: statement timeout for PostgreSQL sessions
    if engine.dialect.name == "postgresql":

        @event.listens_for(engine.sync_engine, "connect")
        def _set_pg_session(dbapi_connection: Any, connection_record: Any) -> None:  # noqa: ARG001
            # asyncpg uses different connection; listen may not fire the same way.
            # Keep hook for psycopg compatibility; asyncpg timeouts via command_timeout later.
            pass

    return engine


def init_database(settings: AppSettings | None = None) -> Database:
    """Create global async engine (call once at startup)."""
    global _database
    settings = settings or get_settings()
    engine = _build_engine(settings)
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    _database = Database(engine, factory, settings)
    logger.info(
        "database_initialized",
        dialect=engine.dialect.name,
        pool_size=settings.database_pool_size,
        env=str(settings.app_env),
    )
    return _database


def get_database() -> Database:
    if _database is None:
        return init_database()
    return _database


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return get_database().session_factory


async def shutdown_database() -> None:
    global _database
    if _database is not None:
        await _database.dispose()
        _database = None


def reset_database_for_tests() -> None:
    """Drop singleton (tests). Caller must dispose engine if needed."""
    global _database
    _database = None


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Async unit-of-work helper for scripts (prefer SqlAlchemyUnitOfWork in app code)."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def validate_database_on_startup(settings: AppSettings, *, strict: bool = False) -> bool:
    """Optionally fail boot if DB is unreachable (staging/production)."""
    db = get_database()
    ok = await db.healthcheck()
    if not ok:
        logger.error("database_startup_validation_failed")
        if strict or settings.is_production:
            raise RuntimeError("Database is unreachable at startup")
    else:
        logger.info("database_startup_validation_ok", pool=db.pool_stats().as_dict())
    return ok
