from __future__ import annotations

from .contracts import IntelligenceRequest, SpecialistDescriptor
from .registry import SpecialistRegistry


class IntelligenceRouter:
    """Resolve a structured capability request to the specialist that owns it."""

    def __init__(self, registry: SpecialistRegistry) -> None:
        self._registry = registry

    def route(self, request: IntelligenceRequest) -> SpecialistDescriptor:
        return self._registry.resolve(request.capability)
