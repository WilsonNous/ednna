from __future__ import annotations

from .contracts import IntelligenceEvent
from .router import EventRouter
from .store import EventStore


class EventService:
    """Persist then route an event through the internal event backbone."""

    def __init__(self, store: EventStore, router: EventRouter) -> None:
        self._store = store
        self._router = router

    def publish(self, event: IntelligenceEvent) -> int:
        self._store.append(event)
        return self._router.route(event)
