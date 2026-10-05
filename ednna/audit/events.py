from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    trace_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str | None = None
    tenant_id: str | None = None
    conversation_id: str | None = None
    specialist_id: str | None = None
    capability: str | None = None
    status: str | None = None
    confidence: float | None = None
    requires_human: bool | None = None
    details: dict[str, Any] = field(default_factory=dict)
