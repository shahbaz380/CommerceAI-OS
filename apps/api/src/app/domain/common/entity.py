"""Base domain entity helpers (no ORM coupling)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class Entity:
    """Identity-based domain entity base."""

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)


@dataclass
class DomainEventMixin:
    """Collect domain events for later dispatch via EventBus."""

    _events: list[Any] = field(default_factory=list, init=False, repr=False)

    def raise_event(self, event: Any) -> None:
        self._events.append(event)

    def pull_events(self) -> list[Any]:
        events = list(self._events)
        self._events.clear()
        return events
