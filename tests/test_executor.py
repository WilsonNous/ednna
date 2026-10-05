from ednna.bootstrap import build_registry
from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse
from ednna.orchestration.discovery import CapabilityDiscovery
from ednna.orchestration.executor import ExecutionContext, PlanExecutor
from ednna.orchestration.gateway import IntelligenceGateway
from ednna.orchestration.planner import Planner
from ednna.orchestration.service import OrchestrationService


class FakeEddyClient:
    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        return IntelligenceResponse(
            specialist_id="eddy",
            capability=request.capability,
            status="success",
            output={"received": request.input},
            trace_id=request.trace_id,
        )

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        raise AssertionError("No action is expected in this test")


def build_executor() -> PlanExecutor:
    registry = build_registry()
    gateway = IntelligenceGateway(registry)
    gateway.register_client("eddy", FakeEddyClient())
    service = OrchestrationService(gateway)
    planner = Planner(CapabilityDiscovery(registry))
    return PlanExecutor(planner, service)


def test_executor_preserves_same_trace_across_plan_and_response():
    executor = build_executor()

    result = executor.execute(
        goal="qual o estado geral da operação EDI",
        input={"scope": "today"},
        context=ExecutionContext(
            user_id="99",
            tenant_id="netunna",
            conversation_id="conv-1",
        ),
    )

    assert result.plan.steps
    assert result.responses
    assert all(response.trace_id == result.trace_id for response in result.responses)
    assert result.responses[0].output == {"received": {"scope": "today"}}


def test_executor_returns_empty_response_set_when_no_capability_matches():
    executor = build_executor()

    result = executor.execute(
        goal="qual é o faturamento do cliente",
        input={},
    )

    assert result.plan.steps == ()
    assert result.responses == ()
    assert result.trace_id
