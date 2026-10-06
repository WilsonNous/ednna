from __future__ import annotations

from ednna.specialists.availability import SpecialistAvailabilityStore

from .contracts import IntelligenceRequest, SpecialistDescriptor
from .registry import SpecialistRegistry


class SpecialistUnavailableError(LookupError):
    pass


class IntelligenceRouter:
    """Resolve a structured capability request to the specialist that owns it."""

    def __init__(
        self,
        registry: SpecialistRegistry,
        availability: SpecialistAvailabilityStore | None = None,
    ) -> None:
        self._registry = registry
        self._availability = availability

    def route(self, request: IntelligenceRequest) -> SpecialistDescriptor:
        specialist = self._registry.resolve(request.capability)

        if (
            self._availability is not None
            and not self._availability.is_routable(specialist.specialist_id)
        ):
            raise SpecialistUnavailableError(
                f"Specialist '{specialist.specialist_id}' is not routable"
            )

        return specialist
