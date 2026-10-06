from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .contracts import IntelligenceEvent


@dataclass(frozen=True)
class OutboxRecord:
    event: IntelligenceEvent
    delivery_status: str = "pending"
    attempts: int = 0
    available_at: datetime | None = None
    delivered_at: datetime | None = None
    last_error_type: str | None = None


class OutboxStore(Protocol):
    def enqueue(self, event: IntelligenceEvent) -> None:
        ...

    def pending(self, limit: int = 100) -> tuple[OutboxRecord, ...]:
        ...

    def mark_delivered(self, event_id: str) -> None:
        ...

    def mark_failed(self, event_id: str, error_type: str) -> None:
        ...


class InMemoryOutboxStore:
    def __init__(self) -> None:
        self._records: dict[str, OutboxRecord] = {}

    def enqueue(self, event: IntelligenceEvent) -> None:
        self._records[event.event_id] = OutboxRecord(event=event)

    def pending(self, limit: int = 100) -> tuple[OutboxRecord, ...]:
        records = [
            record
            for record in self._records.values()
            if record.delivery_status == "pending"
        ]
        return tuple(records[:limit])

    def mark_delivered(self, event_id: str) -> None:
        current = self._records[event_id]
        self._records[event_id] = OutboxRecord(
            event=current.event,
            delivery_status="delivered",
            attempts=current.attempts + 1,
            available_at=current.available_at,
            delivered_at=datetime.utcnow(),
            last_error_type=None,
        )

    def mark_failed(self, event_id: str, error_type: str) -> None:
        current = self._records[event_id]
        self._records[event_id] = OutboxRecord(
            event=current.event,
            delivery_status="pending",
            attempts=current.attempts + 1,
            available_at=current.available_at,
            delivered_at=current.delivered_at,
            last_error_type=error_type,
        )
