"""Event bus foundation tests."""

from __future__ import annotations

import pytest

from app.core.events.bus import DomainEvent, EventBus


@pytest.mark.asyncio
async def test_publish_invokes_handler() -> None:
    bus = EventBus()
    seen: list[str] = []

    async def handler(event: DomainEvent) -> None:
        seen.append(event.name)

    bus.subscribe("test.event", handler)
    await bus.publish(DomainEvent(name="test.event", payload={"a": 1}))
    assert seen == ["test.event"]
