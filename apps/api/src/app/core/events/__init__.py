"""In-process domain event bus foundation."""

from app.core.events.bus import EventBus, DomainEvent, get_event_bus

__all__ = ["DomainEvent", "EventBus", "get_event_bus"]
