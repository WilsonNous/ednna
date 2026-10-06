from __future__ import annotations

from typing import Protocol

from .contracts import IntelligenceEvent
from .outbox import OutboxStore


class EventPublisher(Protocol):
    def publish(self, event: IntelligenceEvent) -> None:
        ...


class OutboxDispatcher:
    """Deliver pending outbox events through a transport publisher."""

    def __init__(self, outbox: OutboxStore, publisher: EventPublisher) -> None:
        self._outbox = outbox
        self._publisher = publisher

    def dispatch(self, limit: int = 100) -> tuple[int, int]:
        delivered = 0
        failed = 0

        for record in self._outbox.pending(limit=limit):
            try:
                self._publisher.publish(record.event)
            except Exception as exc:
                self._outbox.mark_failed(record.event.event_id, type(exc).__name__)
                failed += 1
                continue

            self._outbox.mark_delivered(record.event.event_id)
            delivered += 1

        return delivered, failed
