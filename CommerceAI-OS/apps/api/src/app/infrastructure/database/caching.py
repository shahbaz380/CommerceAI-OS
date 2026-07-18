"""Query caching placeholder — Redis-backed identity cache later.

Does not cache ORM entities in foundation (correctness risk).
Provides a namespaced key builder for future read-through caches.
"""

from __future__ import annotations

from typing import Any

from app.infrastructure.cache.redis_client import RedisClient


class QueryCachePlaceholder:
    """Namespace helper for future cache-aside patterns."""

    def __init__(self, redis: RedisClient, *, ttl_seconds: int = 60) -> None:
        self._redis = redis
        self.ttl_seconds = ttl_seconds

    def entity_key(self, model_name: str, entity_id: Any, workspace_id: Any | None = None) -> str:
        parts = ["entity", model_name, str(entity_id)]
        if workspace_id is not None:
            parts.insert(1, str(workspace_id))
        return self._redis.key(*parts)

    async def get_raw(self, key: str) -> Any:
        return await self._redis.get(key.replace(self._redis.prefix, "", 1) if False else key)

    async def invalidate_prefix(self, *parts: str) -> None:
        # Foundation: no SCAN/delete implementation — document intent only
        return None
