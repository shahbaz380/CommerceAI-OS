"""Async Redis client wrapper (foundation)."""

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis

from app.config.settings import AppSettings, get_settings


class RedisClient:
    def __init__(self, client: Redis, prefix: str) -> None:
        self._client = client
        self.prefix = prefix

    def key(self, *parts: str) -> str:
        return self.prefix + ":".join(parts)

    @property
    def raw(self) -> Redis:
        return self._client

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except Exception:
            return False

    async def get(self, name: str) -> Any:
        return await self._client.get(self.key(name))

    async def set(self, name: str, value: str, ex: int | None = None) -> bool:
        return bool(await self._client.set(self.key(name), value, ex=ex))

    async def close(self) -> None:
        await self._client.aclose()


_redis: RedisClient | None = None


def init_redis(settings: AppSettings | None = None) -> RedisClient:
    global _redis
    settings = settings or get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    _redis = RedisClient(client, settings.redis_prefix)
    return _redis


def get_redis_client() -> RedisClient:
    if _redis is None:
        return init_redis()
    return _redis


async def shutdown_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
