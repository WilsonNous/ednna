import pytest

from ednna.observability.metrics import InMemoryMetricsRecorder
from ednna.observability.observed_service import ObservedOrchestrationService
from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse


class FakeService:
    def query(self, request):
        return IntelligenceResponse(
            specialist_id="eddy",
            capability=request.capability,
            status="success",
            output={},
            requires_human=True,
            trace_id=request.trace_id,
        )

    def action(self, request):
        raise RuntimeError("blocked")


def test_observed_query_records_outcome_and_latency():
    metrics = InMemoryMetricsRecorder()
    service = ObservedOrchestrationService(FakeService(), metrics)

    response = service.query(
        IntelligenceRequest(
            capability="edi.status.get",
            input={},
            trace_id="trace-1",
        )
    )

    assert response.status == "success"
    assert metrics.counter_value(
        "ednna.orchestration.request",
        {"operation": "query", "capability": "edi.status.get"},
    ) == 1
    assert len(metrics.observations("ednna.orchestration.latency_ms")) == 1
    assert metrics.counter_value(
        "ednna.orchestration.requires_human",
        {"specialist": "eddy", "capability": "edi.status.get"},
    ) == 1


def test_observed_error_records_exception_type_without_message():
    metrics = InMemoryMetricsRecorder()
    service = ObservedOrchestrationService(FakeService(), metrics)

    with pytest.raises(RuntimeError):
        service.action(
            IntelligenceRequest(
                capability="edi.operation.execute",
                input={},
            )
        )

    assert metrics.counter_value(
        "ednna.orchestration.error",
        {
            "operation": "action",
            "capability": "edi.operation.execute",
            "error_type": "RuntimeError",
        },
    ) == 1
