from ednna.observability.tracing import ensure_trace
from ednna.orchestration.contracts import IntelligenceRequest


def test_ensure_trace_creates_trace_id_when_missing():
    request = IntelligenceRequest(capability="edi.status.get", input={})

    traced = ensure_trace(request)

    assert traced.trace_id
    assert traced.capability == request.capability


def test_ensure_trace_preserves_existing_trace_id():
    request = IntelligenceRequest(
        capability="edi.status.get",
        input={},
        trace_id="trace-existing",
    )

    traced = ensure_trace(request)

    assert traced.trace_id == "trace-existing"
