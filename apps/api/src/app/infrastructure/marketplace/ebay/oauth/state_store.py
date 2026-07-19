"""OAuth state storage with Redis primary and database fallback."""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.marketplaces.exceptions import OAuthReplayAttack, OAuthStateExpired, OAuthStateInvalid
from app.infrastructure.cache.redis_client import RedisClient, get_redis_client
from app.infrastructure.logging.setup import get_logger
from app.infrastructure.persistence.models.marketplace import MarketplaceOAuthStateModel
from app.infrastructure.persistence.repositories.marketplace import OAuthStateRepository

logger = get_logger("app.marketplace")

STATE_TTL_SECONDS = 900  # 15 minutes


@dataclass(slots=True)
class OAuthStatePayload:
    state: str
    workspace_id: str
    channel: str
    environment: str
    user_id: str
    redirect_uri: str
    connection_id: str | None = None
    nonce: str | None = None
    code_verifier: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> OAuthStatePayload:
        data = json.loads(raw)
        return cls(**data)


class OAuthStateStore:
    """Secure single-use OAuth state with Redis + DB dual write."""

    def __init__(
        self,
        session: AsyncSession,
        redis: RedisClient | None = None,
        *,
        ttl_seconds: int = STATE_TTL_SECONDS,
    ) -> None:
        self.session = session
        self.repo = OAuthStateRepository(session)
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def generate_state() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_nonce() -> str:
        return secrets.token_urlsafe(16)

    def _redis_key(self, state: str) -> str:
        return f"oauth:state:{state}"

    async def create(
        self,
        *,
        workspace_id: UUID,
        channel: str,
        environment: str,
        user_id: UUID,
        redirect_uri: str,
        connection_id: UUID | None = None,
        code_verifier: str | None = None,
    ) -> OAuthStatePayload:
        state = self.generate_state()
        nonce = self.generate_nonce()
        payload = OAuthStatePayload(
            state=state,
            workspace_id=str(workspace_id),
            channel=channel,
            environment=environment,
            user_id=str(user_id),
            redirect_uri=redirect_uri,
            connection_id=str(connection_id) if connection_id else None,
            nonce=nonce,
            code_verifier=code_verifier,
        )
        expires_at = datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)

        # DB fallback (authoritative for multi-instance durability)
        await self.repo.add(
            MarketplaceOAuthStateModel(
                state=state,
                workspace_id=workspace_id,
                channel=channel,
                environment=environment,
                user_id=user_id,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier,
                nonce=nonce,
                connection_id=connection_id,
                expires_at=expires_at,
            )
        )

        # Redis fast path (best-effort)
        try:
            client = self.redis or get_redis_client()
            # store without double-prefix: RedisClient.key adds prefix
            await client.set(f"oauth:state:{state}", payload.to_json(), ex=self.ttl_seconds)
        except Exception as exc:  # noqa: BLE001
            logger.warning("oauth_state_redis_store_failed", error=str(exc))

        return payload

    async def consume(
        self,
        state: str,
        *,
        workspace_id: UUID,
        channel: str,
        user_id: UUID | None = None,
    ) -> OAuthStatePayload:
        if not state or len(state) < 16:
            raise OAuthStateInvalid()

        # Prefer Redis atomic get+delete
        payload: OAuthStatePayload | None = None
        redis_hit = False
        try:
            client = self.redis or get_redis_client()
            key = f"oauth:state:{state}"
            raw = await client.get(key)
            if raw:
                redis_hit = True
                # delete immediately for single-use
                await client.raw.delete(client.key(key))
                payload = OAuthStatePayload.from_json(raw if isinstance(raw, str) else raw.decode())
        except Exception as exc:  # noqa: BLE001
            logger.warning("oauth_state_redis_read_failed", error=str(exc))

        # DB authoritative validation / fallback
        row = await self.repo.get_by_state(state)
        if row is None and payload is None:
            raise OAuthStateInvalid()

        if row is not None:
            if row.consumed_at is not None:
                raise OAuthReplayAttack()
            exp = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=UTC)
            if exp < datetime.now(UTC):
                raise OAuthStateExpired()
            if row.workspace_id != workspace_id:
                raise OAuthStateInvalid("OAuth state workspace mismatch")
            if row.channel != channel:
                raise OAuthStateInvalid("OAuth state channel mismatch")
            if user_id is not None and row.user_id != user_id:
                raise OAuthStateInvalid("OAuth state user mismatch")
            row.consumed_at = datetime.now(UTC)
            await self.session.flush()
            payload = OAuthStatePayload(
                state=row.state,
                workspace_id=str(row.workspace_id),
                channel=row.channel,
                environment=row.environment,
                user_id=str(row.user_id),
                redirect_uri=row.redirect_uri,
                connection_id=str(row.connection_id) if row.connection_id else None,
                nonce=row.nonce,
                code_verifier=row.code_verifier,
            )
        elif payload is not None and redis_hit:
            # Redis-only path still requires workspace/channel match
            if payload.workspace_id != str(workspace_id) or payload.channel != channel:
                raise OAuthStateInvalid("OAuth state mismatch")
            if user_id is not None and payload.user_id != str(user_id):
                raise OAuthStateInvalid("OAuth state user mismatch")

        assert payload is not None
        return payload


class TokenRefreshLock:
    """Distributed lock to prevent concurrent refresh storms."""

    def __init__(self, redis: RedisClient | None = None, *, ttl_seconds: int = 30) -> None:
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def _key(self, connection_id: UUID) -> str:
        return f"oauth:refresh-lock:{connection_id}"

    async def acquire(self, connection_id: UUID) -> bool:
        try:
            client = self.redis or get_redis_client()
            # SET NX EX
            ok = await client.raw.set(
                client.key(self._key(connection_id)),
                "1",
                nx=True,
                ex=self.ttl_seconds,
            )
            return bool(ok)
        except Exception as exc:  # noqa: BLE001
            logger.warning("refresh_lock_unavailable", error=str(exc))
            return True  # fail open to local path if Redis down

    async def release(self, connection_id: UUID) -> None:
        try:
            client = self.redis or get_redis_client()
            await client.raw.delete(client.key(self._key(connection_id)))
        except Exception as exc:  # noqa: BLE001
            logger.warning("refresh_lock_release_failed", error=str(exc))
