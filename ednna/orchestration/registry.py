from __future__ import annotations

from .contracts import SpecialistDescriptor


class CapabilityNotFoundError(LookupError):
    pass


class DuplicateCapabilityError(ValueError):
    pass


class SpecialistRegistry:
    """In-memory registry for specialist capabilities.

    Persistence/discovery will be added later. Keeping the interface small allows
    EDNNA to evolve without coupling the orchestrator to any specialist internals.
    """

    def __init__(self) -> None:
        self._specialists: dict[str, SpecialistDescriptor] = {}
        self._capability_owners: dict[str, str] = {}

    def register(self, specialist: SpecialistDescriptor) -> None:
        for capability in specialist.capabilities:
            owner = self._capability_owners.get(capability.name)
            if owner and owner != specialist.specialist_id:
                raise DuplicateCapabilityError(
                    f"Capability '{capability.name}' is already owned by '{owner}'"
                )

        self._specialists[specialist.specialist_id] = specialist
        for capability in specialist.capabilities:
            self._capability_owners[capability.name] = specialist.specialist_id

    def get_specialist(self, specialist_id: str) -> SpecialistDescriptor | None:
        return self._specialists.get(specialist_id)

    def resolve(self, capability_name: str) -> SpecialistDescriptor:
        specialist_id = self._capability_owners.get(capability_name)
        if specialist_id is None:
            raise CapabilityNotFoundError(
                f"No specialist is registered for capability '{capability_name}'"
            )
        return self._specialists[specialist_id]

    def list_specialists(self) -> tuple[SpecialistDescriptor, ...]:
        return tuple(self._specialists.values())
