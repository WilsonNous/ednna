from ednna.governance.policies import ActionNotAuthorizedError
from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse
from ednna.orchestration.gateway import IntelligenceGateway
from ednna.orchestration.registry import SpecialistRegistry
from ednna.orchestration.service import OrchestrationService
from ednna.specialists.eddy import EDDY_DESCRIPTOR

import pytest


class FakeClient:
    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        return IntelligenceResponse(
            specialist_id="eddy",
            capability=request.capability,
            status="success",
            output={"trace_id": request.trace_id},
            trace_id=request.trace_id,
        )

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        raise AssertionError("Action transport should not be reached without explicit policy")


def build_service() -> OrchestrationService:
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    gateway = IntelligenceGateway(registry)
    gateway.register_client("eddy", FakeClient())
    return OrchestrationService(gateway)


def test_query_adds_trace_before_dispatch():
    service = build_service()

    response = service.query(IntelligenceRequest(capability="edi.status.get", input={}))

    assert response.trace_id
    assert response.output["trace_id"] == response.trace_id


def test_action_is_blocked_before_transport_by_default():
    service = build_service()

    with pytest.raises(ActionNotAuthorizedError):
        service.action(IntelligenceRequest(capability="edi.status.get", input={}))
