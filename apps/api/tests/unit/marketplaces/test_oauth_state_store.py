"""OAuth state store unit tests (DB path, no Redis required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.marketplaces.exceptions import OAuthReplayAttack, OAuthStateExpired, OAuthStateInvalid
from app.infrastructure.database.base import Base
from app.infrastructure.marketplace.ebay.oauth.state_store import OAuthStateStore
from app.infrastructure.persistence.models import identity as _i  # noqa: F401
from app.infrastructure.persistence.models import marketplace as _m  # noqa: F401
from app.infrastructure.persistence.models import tenancy as _t  # noqa: F401
from app.infrastructure.persistence.models.identity import UserModel


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        # minimal user for FK
        from app.infrastructure.security.passwords import get_password_hasher

        u = UserModel(
            email="oauth@example.com",
            password_hash=get_password_hasher().hash("Str0ng!Passw0rd"),
            is_active=True,
        )
        s.add(u)
        await s.flush()
        yield s
        await s.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_state_create_and_consume(session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    # force redis failure path
    store = OAuthStateStore(session)

    async def boom(*args, **kwargs):
        raise RuntimeError("redis down")

    monkeypatch.setattr(store, "redis", None)
    # patch get_redis_client used inside
    import app.infrastructure.marketplace.ebay.oauth.state_store as mod

    monkeypatch.setattr(mod, "get_redis_client", lambda: type("R", (), {"set": boom, "get": boom, "raw": type("X", (), {"delete": boom})(), "key": lambda self, k: k})())

    user_id = (await session.execute(__import__("sqlalchemy").select(UserModel))).scalar_one().id
    ws = uuid.uuid4()
    payload = await store.create(
        workspace_id=ws,
        channel="ebay",
        environment="sandbox",
        user_id=user_id,
        redirect_uri="https://app.example.com/cb",
        connection_id=uuid.uuid4(),
    )
    assert payload.state
    assert payload.nonce

    consumed = await store.consume(payload.state, workspace_id=ws, channel="ebay", user_id=user_id)
    assert consumed.workspace_id == str(ws)

    with pytest.raises(OAuthReplayAttack):
        await store.consume(payload.state, workspace_id=ws, channel="ebay", user_id=user_id)


@pytest.mark.asyncio
async def test_state_expired(session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    import app.infrastructure.marketplace.ebay.oauth.state_store as mod

    async def boom(*a, **k):
        raise RuntimeError("redis down")

    monkeypatch.setattr(mod, "get_redis_client", lambda: type("R", (), {"set": boom, "get": boom, "raw": type("X", (), {"delete": boom})(), "key": lambda s, k: k})())
    store = OAuthStateStore(session, ttl_seconds=1)
    user_id = (await session.execute(__import__("sqlalchemy").select(UserModel))).scalar_one().id
    ws = uuid.uuid4()
    payload = await store.create(
        workspace_id=ws,
        channel="ebay",
        environment="sandbox",
        user_id=user_id,
        redirect_uri="https://app.example.com/cb",
    )
    # expire row manually
    from app.infrastructure.persistence.repositories.marketplace import OAuthStateRepository

    row = await OAuthStateRepository(session).get_by_state(payload.state)
    assert row is not None
    row.expires_at = datetime.now(UTC) - timedelta(seconds=5)
    await session.flush()
    with pytest.raises(OAuthStateExpired):
        await store.consume(payload.state, workspace_id=ws, channel="ebay")


@pytest.mark.asyncio
async def test_state_invalid(session: AsyncSession) -> None:
    store = OAuthStateStore(session)
    with pytest.raises(OAuthStateInvalid):
        await store.consume("short", workspace_id=uuid.uuid4(), channel="ebay")
