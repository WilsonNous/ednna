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


def test_uncertain_action_can_be_manually_reconciled():
    ledger = InMemoryActionExecutionLedger()
    ledger.start(
        idempotency_key="action-3",
        trace_id="trace-3",
        capability="edi.operation.execute",
        tenant_id="tenant-1",
    )
    ledger.uncertain("action-3", "SpecialistTransportError")

    reconciled = ledger.reconcile(
        "action-3",
        ActionExecutionStatus.RECONCILED_SUCCEEDED,
        reconciled_by="reviewer-1",
        note="Confirmed in specialist audit",
        reference="eddy:audit:123",
    )

    assert reconciled.status is ActionExecutionStatus.RECONCILED_SUCCEEDED
    assert reconciled.reconciled_by == "reviewer-1"
    assert reconciled.reconciliation_reference == "eddy:audit:123"
    assert reconciled.reconciled_at is not None


def test_non_uncertain_action_cannot_be_reconciled():
    import pytest

    from ednna.governance.action_ledger import ActionExecutionNotReconcilableError

    ledger = InMemoryActionExecutionLedger()
    ledger.start(
        idempotency_key="action-4",
        trace_id="trace-4",
        capability="edi.operation.execute",
    )
    ledger.succeed(
        "action-4",
        specialist_id="eddy",
        response_status="success",
        evidence_count=1,
    )

    with pytest.raises(ActionExecutionNotReconcilableError):
        ledger.reconcile(
            "action-4",
            ActionExecutionStatus.RECONCILED_NOT_EXECUTED,
            reconciled_by="reviewer-1",
            note="Invalid transition",
            reference="audit:invalid",
        )
