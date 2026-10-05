from ednna.audit.recorder import AuditRecorder
from ednna.audit.store import InMemoryAuditStore
from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse


def test_audit_recorder_stores_request_and_response_without_payload_contents():
    store = InMemoryAuditStore()
    recorder = AuditRecorder(store)
    request = IntelligenceRequest(
        capability="edi.status.get",
        input={"sensitive": "value"},
        user_id="99",
        tenant_id="netunna",
        conversation_id="conv-1",
        trace_id="trace-1",
    )
    response = IntelligenceResponse(
        specialist_id="eddy",
        capability="edi.status.get",
        status="success",
        output={"secret": "must-not-be-audited"},
        confidence=0.98,
        evidence=({"type": "operation", "id": "1"},),
        trace_id="trace-1",
    )

    recorder.record_request("query.requested", request)
    recorder.record_response("query.completed", request, response)

    events = store.list_by_trace("trace-1")
    assert len(events) == 2
    assert events[0].details == {"input_keys": ["sensitive"]}
    assert "value" not in str(events)
    assert "must-not-be-audited" not in str(events)
    assert events[1].details["evidence_count"] == 1
