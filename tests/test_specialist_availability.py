from ednna.specialists.availability import (
    SpecialistAvailability,
    SpecialistAvailabilityRegistry,
)


def test_unknown_specialist_is_not_routable_when_availability_is_enforced():
    availability = SpecialistAvailabilityRegistry()

    assert availability.is_routable("eddy") is False
    assert availability.get("eddy").status is SpecialistAvailability.UNKNOWN


def test_ready_and_degraded_are_routable():
    availability = SpecialistAvailabilityRegistry()
    availability.set("eddy", SpecialistAvailability.READY)
    availability.set("finance", SpecialistAvailability.DEGRADED)

    assert availability.is_routable("eddy") is True
    assert availability.is_routable("finance") is True


def test_quarantine_removes_specialist_from_routing():
    availability = SpecialistAvailabilityRegistry()
    availability.set("eddy", SpecialistAvailability.READY)

    availability.quarantine("eddy", "contract_mismatch")

    state = availability.get("eddy")
    assert state.status is SpecialistAvailability.QUARANTINED
    assert state.reason_code == "contract_mismatch"
    assert availability.is_routable("eddy") is False
