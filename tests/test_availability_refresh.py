from ednna.orchestration.registry import SpecialistRegistry
from ednna.specialists.availability import (
    SpecialistAvailability,
    SpecialistAvailabilityRegistry,
)
from ednna.specialists.availability_refresh import SpecialistAvailabilityRefresher
from ednna.specialists.eddy import EDDY_DESCRIPTOR
from ednna.specialists.handshake import SpecialistHandshake


class FakeClient:
    def __init__(self, handshake=None, error=None):
        self._handshake = handshake
        self._error = error

    def handshake(self):
        if self._error:
            raise self._error
        return self._handshake


def build_registry():
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    return registry


def capabilities():
    return tuple(capability.name for capability in EDDY_DESCRIPTOR.capabilities)


def test_refresh_marks_ready_specialist_routable():
    availability = SpecialistAvailabilityRegistry()
    client = FakeClient(
        SpecialistHandshake(
            specialist_id="eddy",
            contract_version="1",
            capabilities=capabilities(),
            status="ready",
        )
    )

    SpecialistAvailabilityRefresher(
        build_registry(),
        availability,
        {"eddy": client},
    ).refresh()

    assert availability.get("eddy").status is SpecialistAvailability.READY


def test_refresh_preserves_degraded_as_routable_state():
    availability = SpecialistAvailabilityRegistry()
    client = FakeClient(
        SpecialistHandshake(
            specialist_id="eddy",
            contract_version="1",
            capabilities=capabilities(),
            status="degraded",
        )
    )

    SpecialistAvailabilityRefresher(
        build_registry(),
        availability,
        {"eddy": client},
    ).refresh()

    state = availability.get("eddy")
    assert state.status is SpecialistAvailability.DEGRADED
    assert state.reason_code == "remote_degraded"
    assert availability.is_routable("eddy") is True


def test_refresh_quarantines_contract_mismatch():
    availability = SpecialistAvailabilityRegistry()
    client = FakeClient(
        SpecialistHandshake(
            specialist_id="other",
            contract_version="1",
            capabilities=capabilities(),
            status="ready",
        )
    )

    SpecialistAvailabilityRefresher(
        build_registry(),
        availability,
        {"eddy": client},
    ).refresh()

    state = availability.get("eddy")
    assert state.status is SpecialistAvailability.QUARANTINED
    assert state.reason_code == "handshake_incompatible"


def test_refresh_marks_transport_failure_unavailable():
    availability = SpecialistAvailabilityRegistry()
    client = FakeClient(error=RuntimeError("network down"))

    SpecialistAvailabilityRefresher(
        build_registry(),
        availability,
        {"eddy": client},
    ).refresh()

    state = availability.get("eddy")
    assert state.status is SpecialistAvailability.UNAVAILABLE
    assert state.reason_code == "handshake_failed"
