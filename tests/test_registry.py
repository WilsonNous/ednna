import pytest

from ednna.orchestration.contracts import Capability, OperationKind, SpecialistDescriptor
from ednna.orchestration.registry import (
    CapabilityNotFoundError,
    DuplicateCapabilityError,
    SpecialistRegistry,
)
from ednna.specialists.eddy import EDDY_DESCRIPTOR


def test_registry_resolves_eddy_capability():
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)

    specialist = registry.resolve("edi.issue.inspect")

    assert specialist.specialist_id == "eddy"
    assert specialist.domain == "edi"


def test_registry_rejects_duplicate_capability_owner():
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    another = SpecialistDescriptor(
        specialist_id="other",
        name="Other",
        domain="test",
        description="test",
        capabilities=(
            Capability("edi.issue.inspect", OperationKind.QUERY),
        ),
    )

    with pytest.raises(DuplicateCapabilityError):
        registry.register(another)


def test_registry_raises_for_unknown_capability():
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)

    with pytest.raises(CapabilityNotFoundError):
        registry.resolve("finance.status.get")
