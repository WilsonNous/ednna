import pytest

from ednna.bootstrap import build_registry
from ednna.orchestration.contracts import IntelligenceRequest
from ednna.orchestration.discovery import CapabilityDiscovery
from ednna.orchestration.router import IntelligenceRouter, SpecialistUnavailableError
from ednna.specialists.availability import (
    SpecialistAvailability,
    SpecialistAvailabilityRegistry,
)


def test_discovery_excludes_quarantined_specialist():
    registry = build_registry()
    availability = SpecialistAvailabilityRegistry()
    availability.quarantine("eddy", "contract_mismatch")
    discovery = CapabilityDiscovery(registry, availability=availability)

    matches = discovery.search("consultar chamado EDI")

    assert matches == ()


def test_router_blocks_unavailable_specialist():
    registry = build_registry()
    availability = SpecialistAvailabilityRegistry()
    availability.set("eddy", SpecialistAvailability.UNAVAILABLE)
    router = IntelligenceRouter(registry, availability=availability)

    with pytest.raises(SpecialistUnavailableError):
        router.route(
            IntelligenceRequest(
                capability="edi.status.get",
                input={},
            )
        )


def test_router_allows_ready_specialist():
    registry = build_registry()
    availability = SpecialistAvailabilityRegistry()
    availability.set("eddy", SpecialistAvailability.READY)
    router = IntelligenceRouter(registry, availability=availability)

    specialist = router.route(
        IntelligenceRequest(
            capability="edi.status.get",
            input={},
        )
    )

    assert specialist.specialist_id == "eddy"
