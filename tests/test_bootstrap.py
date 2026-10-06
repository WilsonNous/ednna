from ednna.bootstrap import build_gateway, build_registry, build_router
from ednna.orchestration.contracts import IntelligenceRequest


def test_bootstrap_registers_eddy():
    registry = build_registry()

    specialist = registry.resolve("edi.status.get")

    assert specialist.specialist_id == "eddy"


def test_bootstrap_router_uses_registered_capabilities():
    router = build_router()

    specialist = router.route(IntelligenceRequest(capability="edi.issue.inspect", input={}))

    assert specialist.name == "EDDY"


def test_bootstrap_gateway_starts_without_transport_clients():
    gateway = build_gateway()

    assert gateway is not None
