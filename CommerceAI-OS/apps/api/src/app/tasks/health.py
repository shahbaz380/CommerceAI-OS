"""Background task foundation — health ping task only."""

from __future__ import annotations

from datetime import UTC, datetime

from app.infrastructure.messaging.celery_app import celery_app


@celery_app.task(name="app.tasks.health.ping")
def ping() -> dict[str, str]:
    """Lightweight task to validate Celery wiring."""
    return {"status": "pong", "at": datetime.now(UTC).isoformat()}
