import pytest

from ednna.specialists.eddy import EDDY_DESCRIPTOR
from ednna.specialists.handshake import (
    SpecialistHandshake,
    SpecialistHandshakeError,
    validate_handshake,
)
from ednna.specialists.protocol import UnsupportedContractVersionError


def test_handshake_accepts_matching_identity_version_and_capabilities():
    handshake = SpecialistHandshake(
        specialist_id="eddy",
        contract_version="1",
        capabilities=tuple(
            capability.name
            for capability in EDDY_DESCRIPTOR.capabilities
        ),
        status="ready",
    )

    validate_handshake(EDDY_DESCRIPTOR, handshake)


def test_handshake_rejects_wrong_specialist_identity():
    handshake = SpecialistHandshake(
        specialist_id="other",
        contract_version="1",
        capabilities=tuple(
            capability.name
            for capability in EDDY_DESCRIPTOR.capabilities
        ),
    )

    with pytest.raises(SpecialistHandshakeError):
        validate_handshake(EDDY_DESCRIPTOR, handshake)


def test_handshake_rejects_missing_declared_capability():
    handshake = SpecialistHandshake(
        specialist_id="eddy",
        contract_version="1",
        capabilities=("edi.status.get",),
    )

    with pytest.raises(SpecialistHandshakeError):
        validate_handshake(EDDY_DESCRIPTOR, handshake)


def test_handshake_rejects_incompatible_contract_version():
    handshake = SpecialistHandshake(
        specialist_id="eddy",
        contract_version="2",
        capabilities=tuple(
            capability.name
            for capability in EDDY_DESCRIPTOR.capabilities
        ),
    )

    with pytest.raises(UnsupportedContractVersionError):
        validate_handshake(EDDY_DESCRIPTOR, handshake)
