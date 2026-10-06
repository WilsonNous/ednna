from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class IntelligenceEvent:
    event_id: str
    event_type: str
    source: str
    trace_id: str
    tenant_id: str | None = None
    subject: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: str,
        source: str,
        trace_id: str,
        tenant_id: str | None = None,
        subject: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> "IntelligenceEvent":
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            source=source,
            trace_id=trace_id,
            tenant_id=tenant_id,
            subject=subject,
            data=data or {},
        )
