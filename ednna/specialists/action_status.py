from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SpecialistActionState(str, Enum):
    SUCCEEDED = "succeeded"
    NOT_EXECUTED = "not_executed"
    IN_PROGRESS = "in_progress"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SpecialistActionStatus:
    specialist_id: str
    idempotency_key: str
    state: SpecialistActionState
    trace_id: str | None = None
    evidence: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    reference: str | None = None
