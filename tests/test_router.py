from ednna.orchestration.contracts import IntelligenceRequest
from ednna.orchestration.registry import SpecialistRegistry
from ednna.orchestration.router import IntelligenceRouter
from ednna.specialists.eddy import EDDY_DESCRIPTOR


def test_router_routes_structured_request_by_capability():
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    router = IntelligenceRouter(registry)

    request = IntelligenceRequest(
        capability="edi.status.get",
        input={},
        user_id="99",
        tenant_id="netunna",
        trace_id="trace-test",
    )

    specialist = router.route(request)

    assert specialist.specialist_id == "eddy"
