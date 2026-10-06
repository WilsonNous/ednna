from __future__ import annotations

from collections.abc import Callable

from .contracts import IntelligenceEvent


EventHandler = Callable[[IntelligenceEvent], None]


class EventHandlerNotFoundError(LookupError):
    pass


class EventRouter:
    """Route known event types to registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def route(self, event: IntelligenceEvent) -> int:
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            handler(event)
        return len(handlers)
