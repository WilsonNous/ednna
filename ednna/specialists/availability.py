from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SpecialistAvailability(str, Enum):
    UNKNOWN = "unknown"
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    QUARANTINED = "quarantined"


@dataclass(frozen=True)
class SpecialistAvailabilityState:
    specialist_id: str
    status: SpecialistAvailability
    reason_code: str | None = None


class SpecialistAvailabilityRegistry:
    """Runtime availability separate from static specialist capability metadata."""

    def __init__(self) -> None:
        self._states: dict[str, SpecialistAvailabilityState] = {}

    def set(
        self,
        specialist_id: str,
        status: SpecialistAvailability,
        reason_code: str | None = None,
    ) -> None:
        self._states[specialist_id] = SpecialistAvailabilityState(
            specialist_id=specialist_id,
            status=status,
            reason_code=reason_code,
        )

    def get(self, specialist_id: str) -> SpecialistAvailabilityState:
        return self._states.get(
            specialist_id,
            SpecialistAvailabilityState(
                specialist_id=specialist_id,
                status=SpecialistAvailability.UNKNOWN,
            ),
        )

    def is_routable(self, specialist_id: str) -> bool:
        return self.get(specialist_id).status in {
            SpecialistAvailability.READY,
            SpecialistAvailability.DEGRADED,
        }

    def quarantine(self, specialist_id: str, reason_code: str) -> None:
        self.set(
            specialist_id,
            SpecialistAvailability.QUARANTINED,
            reason_code=reason_code,
        )
