import pytest

from ednna.orchestration.contracts import (
    IntelligenceRequest,
    IntelligenceResponse,
    OperationKind,
)
from ednna.orchestration.gateway import (
    CapabilityKindMismatchError,
    IntelligenceGateway,
    SpecialistClientNotFoundError,
)
from ednna.orchestration.registry import SpecialistRegistry
from ednna.specialists.eddy import EDDY_DESCRIPTOR


class FakeEddyClient:
    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        return IntelligenceResponse(
            specialist_id="eddy",
            capability=request.capability,
            status="success",
            output={"healthy": True},
            confidence=1.0,
            trace_id=request.trace_id,
        )

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        raise AssertionError("No EDDY action should be executed in this foundation test")


def build_gateway() -> IntelligenceGateway:
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    gateway = IntelligenceGateway(registry)
    gateway.register_client("eddy", FakeEddyClient())
    return gateway


def test_gateway_dispatches_query_to_registered_specialist_client():
    gateway = build_gateway()
    request = IntelligenceRequest(
        capability="edi.status.get",
        input={},
        trace_id="trace-1",
    )

    response = gateway.dispatch(request, OperationKind.QUERY)

    assert response.specialist_id == "eddy"
    assert response.output == {"healthy": True}
    assert response.trace_id == "trace-1"


def test_gateway_blocks_operation_kind_mismatch():
    gateway = build_gateway()
    request = IntelligenceRequest(capability="edi.status.get", input={})

    with pytest.raises(CapabilityKindMismatchError):
        gateway.dispatch(request, OperationKind.ACTION)


def test_gateway_requires_registered_transport_client():
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    gateway = IntelligenceGateway(registry)
    request = IntelligenceRequest(capability="edi.status.get", input={})

    with pytest.raises(SpecialistClientNotFoundError):
        gateway.dispatch(request, OperationKind.QUERY)
