from __future__ import annotations

from typing import Protocol

from .contracts import IntelligenceEvent


class EventStore(Protocol):
    def append(self, event: IntelligenceEvent) -> None:
        ...

    def list_by_trace(self, trace_id: str) -> tuple[IntelligenceEvent, ...]:
        ...


class InMemoryEventStore:
    def __init__(self) -> None:
        self._events: list[IntelligenceEvent] = []

    def append(self, event: IntelligenceEvent) -> None:
        self._events.append(event)

    def list_by_trace(self, trace_id: str) -> tuple[IntelligenceEvent, ...]:
        return tuple(event for event in self._events if event.trace_id == trace_id)
