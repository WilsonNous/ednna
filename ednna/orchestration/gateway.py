from __future__ import annotations

from typing import Protocol

from ednna.specialists.availability import SpecialistAvailabilityStore

from .contracts import IntelligenceRequest, IntelligenceResponse, OperationKind
from .registry import SpecialistRegistry
from .router import SpecialistUnavailableError


class SpecialistClient(Protocol):
    """Transport-agnostic client implemented by each specialist adapter."""

    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        ...

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        ...


class SpecialistClientNotFoundError(LookupError):
    pass


class CapabilityKindMismatchError(ValueError):
    pass


class IntelligenceGateway:
    """Dispatch structured requests without exposing specialist internals to EDNNA."""

    def __init__(
        self,
        registry: SpecialistRegistry,
        availability: SpecialistAvailabilityStore | None = None,
    ) -> None:
        self._registry = registry
        self._availability = availability
        self._clients: dict[str, SpecialistClient] = {}

    def register_client(self, specialist_id: str, client: SpecialistClient) -> None:
        if self._registry.get_specialist(specialist_id) is None:
            raise SpecialistClientNotFoundError(
                f"Specialist '{specialist_id}' must be registered before its client"
            )
        self._clients[specialist_id] = client

    def dispatch(
        self,
        request: IntelligenceRequest,
        operation: OperationKind,
    ) -> IntelligenceResponse:
        specialist = self._registry.resolve(request.capability)

        if (
            self._availability is not None
            and not self._availability.is_routable(specialist.specialist_id)
        ):
            raise SpecialistUnavailableError(
                f"Specialist '{specialist.specialist_id}' is not routable"
            )

        capability = next(
            item for item in specialist.capabilities if item.name == request.capability
        )

        if capability.kind != operation:
            raise CapabilityKindMismatchError(
                f"Capability '{request.capability}' is '{capability.kind.value}', "
                f"not '{operation.value}'"
            )

        client = self._clients.get(specialist.specialist_id)
        if client is None:
            raise SpecialistClientNotFoundError(
                f"No client is configured for specialist '{specialist.specialist_id}'"
            )

        if operation is OperationKind.QUERY:
            return client.query(request)
        return client.action(request)
