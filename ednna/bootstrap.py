from __future__ import annotations

from .orchestration.gateway import IntelligenceGateway, SpecialistClient
from .orchestration.registry import SpecialistRegistry
from .orchestration.router import IntelligenceRouter
from .specialists.catalog import (
    build_manifest_clients,
    load_catalog_from_env,
    register_catalog,
)
from .specialists.eddy import EDDY_DESCRIPTOR
from .specialists.feature_flags import eddy_enabled


def build_registry() -> SpecialistRegistry:
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    register_catalog(registry, load_catalog_from_env())
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


def build_catalog_gateway() -> IntelligenceGateway:
    manifests = load_catalog_from_env()
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    register_catalog(registry, manifests)

    clients = build_manifest_clients(manifests)
    if eddy_enabled():
        from .specialists.eddy_client import build_eddy_client

        clients["eddy"] = build_eddy_client()

    return build_gateway(clients=clients, registry=registry)


def build_eddy_gateway() -> IntelligenceGateway:
    """Build a gateway with the EDDY HTTP transport enabled by environment config."""
    from .specialists.eddy_client import build_eddy_client

    return build_gateway(clients={"eddy": build_eddy_client()})


def build_planner():
    """Build the deterministic capability planner."""
    from .orchestration.discovery import CapabilityDiscovery
    from .orchestration.planner import Planner

    return Planner(CapabilityDiscovery(build_registry()))


def build_executor(clients=None):
    """Build the governed planner/executor pipeline."""
    from .governance.policies import GovernancePolicyRegistry
    from .orchestration.discovery import CapabilityDiscovery
    from .orchestration.executor import PlanExecutor
    from .orchestration.planner import Planner
    from .orchestration.service import OrchestrationService

    registry = build_registry()
    gateway = build_gateway(clients=clients, registry=registry)
    planner = Planner(CapabilityDiscovery(registry))
    service = OrchestrationService(gateway, GovernancePolicyRegistry())
    return PlanExecutor(planner, service)


def build_multiagent_components() -> tuple[SpecialistRegistry, IntelligenceGateway]:
    """Build a registry and gateway from the same active specialist catalog."""
    manifests = load_catalog_from_env()
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    register_catalog(registry, manifests)

    clients = build_manifest_clients(manifests)
    if eddy_enabled():
        from .specialists.eddy_client import build_eddy_client

        clients["eddy"] = build_eddy_client()

    return registry, build_gateway(clients=clients, registry=registry)
