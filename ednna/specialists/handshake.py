from __future__ import annotations

from dataclasses import dataclass

from ednna.orchestration.contracts import SpecialistDescriptor
from ednna.specialists.protocol import CONTRACT_VERSION, validate_contract_version


@dataclass(frozen=True)
class SpecialistHandshake:
    specialist_id: str
    contract_version: str
    capabilities: tuple[str, ...]
    status: str = "ready"


class SpecialistHandshakeError(RuntimeError):
    pass


def validate_handshake(
    descriptor: SpecialistDescriptor,
    handshake: SpecialistHandshake,
) -> None:
    validate_contract_version(handshake.contract_version)

    if handshake.specialist_id != descriptor.specialist_id:
        raise SpecialistHandshakeError(
            "Remote specialist identity does not match configured specialist"
        )

    declared = {capability.name for capability in descriptor.capabilities}
    remote = set(handshake.capabilities)
    missing = sorted(declared - remote)

    if missing:
        raise SpecialistHandshakeError(
            "Remote specialist is missing declared capabilities: "
            + ",".join(missing)
        )

    if handshake.status != "ready":
        raise SpecialistHandshakeError(
            f"Remote specialist is not ready: {handshake.status}"
        )


def expected_contract_version() -> str:
    return CONTRACT_VERSION
