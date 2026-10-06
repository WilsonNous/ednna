from __future__ import annotations

from typing import Protocol

from ednna.orchestration.registry import SpecialistRegistry
from ednna.specialists.availability import (
    SpecialistAvailability,
    SpecialistAvailabilityRegistry,
)
from ednna.specialists.handshake import (
    SpecialistHandshake,
    SpecialistHandshakeError,
    validate_handshake_compatibility,
)
from ednna.specialists.protocol import UnsupportedContractVersionError


class HandshakeClient(Protocol):
    def handshake(self) -> SpecialistHandshake:
        ...


class SpecialistAvailabilityRefresher:
    """Refresh runtime availability using side-effect-free specialist handshakes."""

    def __init__(
        self,
        registry: SpecialistRegistry,
        availability: SpecialistAvailabilityRegistry,
        clients: dict[str, HandshakeClient],
    ) -> None:
        self._registry = registry
        self._availability = availability
        self._clients = clients

    def refresh(self) -> SpecialistAvailabilityRegistry:
        for specialist in self._registry.list_specialists():
            client = self._clients.get(specialist.specialist_id)
            if client is None:
                continue

            try:
                handshake = client.handshake()
                validate_handshake_compatibility(specialist, handshake)
            except (SpecialistHandshakeError, UnsupportedContractVersionError):
                self._availability.quarantine(
                    specialist.specialist_id,
                    "handshake_incompatible",
                )
                continue
            except Exception:
                self._availability.set(
                    specialist.specialist_id,
                    SpecialistAvailability.UNAVAILABLE,
                    reason_code="handshake_failed",
                )
                continue

            status = handshake.status.strip().lower()
            if status == "ready":
                self._availability.set(
                    specialist.specialist_id,
                    SpecialistAvailability.READY,
                )
            elif status == "degraded":
                self._availability.set(
                    specialist.specialist_id,
                    SpecialistAvailability.DEGRADED,
                    reason_code="remote_degraded",
                )
            else:
                self._availability.set(
                    specialist.specialist_id,
                    SpecialistAvailability.UNAVAILABLE,
                    reason_code="remote_unavailable",
                )

        return self._availability
