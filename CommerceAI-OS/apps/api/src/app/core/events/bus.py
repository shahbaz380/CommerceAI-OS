"""Simple async domain event bus (in-process).

Future: outbox pattern + broker publish for microservices.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.infrastructure.logging.setup import get_logger

logger = get_logger("app")

EventHandler = Callable[["DomainEvent"], Awaitable[None]]


@dataclass(slots=True)
class DomainEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid4().hex)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    workspace_id: str | None = None
    correlation_id: str | None = None


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)
        logger.debug("event_subscribed", event_name=event_name, handler=handler.__name__)

    async def publish(self, event: DomainEvent) -> None:
        handlers = list(self._handlers.get(event.name, []))
        # wildcard listeners
        handlers.extend(self._handlers.get("*", []))
        logger.info(
            "event_published",
            event_name=event.name,
            event_id=event.event_id,
            handlers=len(handlers),
        )
        for handler in handlers:
            await handler(event)


_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
