from ednna.governance.action_ledger import (
    ActionExecutionStatus,
    InMemoryActionExecutionLedger,
)


def test_action_ledger_tracks_successful_execution():
    ledger = InMemoryActionExecutionLedger()

    started = ledger.start(
        idempotency_key="action-1",
        trace_id="trace-1",
        capability="edi.operation.execute",
        tenant_id="tenant-1",
        requested_by="operator-1",
    )
    succeeded = ledger.succeed(
        "action-1",
        specialist_id="eddy",
        response_status="success",
        evidence_count=2,
    )

    assert started.status is ActionExecutionStatus.STARTED
    assert succeeded.status is ActionExecutionStatus.SUCCEEDED
    assert succeeded.specialist_id == "eddy"
    assert succeeded.evidence_count == 2


def test_action_ledger_marks_transport_failure_as_uncertain():
    ledger = InMemoryActionExecutionLedger()
    ledger.start(
        idempotency_key="action-2",
        trace_id="trace-2",
        capability="edi.operation.execute",
    )

    uncertain = ledger.uncertain("action-2", "SpecialistTransportError")

    assert uncertain.status is ActionExecutionStatus.UNCERTAIN
    assert uncertain.error_type == "SpecialistTransportError"
