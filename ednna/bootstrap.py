from __future__ import annotations

from .orchestration.gateway import IntelligenceGateway, SpecialistClient
from .orchestration.registry import SpecialistRegistry
from .orchestration.router import IntelligenceRouter
from .specialists.eddy import EDDY_DESCRIPTOR


def build_registry() -> SpecialistRegistry:
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    return registry


def build_router(registry: SpecialistRegistry | None = None) -> IntelligenceRouter:
    return IntelligenceRouter(registry or build_registry())


def build_gateway(
    clients: dict[str, SpecialistClient] | None = None,
    registry: SpecialistRegistry | None = None,
) -> IntelligenceGateway:
    active_registry = registry or build_registry()
    gateway = IntelligenceGateway(active_registry)

    for specialist_id, client in (clients or {}).items():
        gateway.register_client(specialist_id, client)

    return gateway
