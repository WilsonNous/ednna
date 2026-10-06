from __future__ import annotations

from typing import Protocol

from .events import AuditEvent


class AuditStore(Protocol):
    def append(self, event: AuditEvent) -> None:
        ...

    def list_by_trace(self, trace_id: str) -> tuple[AuditEvent, ...]:
        ...


class InMemoryAuditStore:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_by_trace(self, trace_id: str) -> tuple[AuditEvent, ...]:
        return tuple(event for event in self._events if event.trace_id == trace_id)
