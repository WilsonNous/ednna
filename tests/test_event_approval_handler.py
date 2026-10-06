from ednna.events.approval_handler import ApprovalEventHandler
from ednna.events.contracts import IntelligenceEvent
from ednna.governance.approvals import InMemoryApprovalStore


def test_mapped_event_creates_human_approval_for_fixed_capability():
    approvals = InMemoryApprovalStore()
    handler = ApprovalEventHandler(approvals)
    event = IntelligenceEvent.create(
        event_type="edi.operation.approval_required",
        source="eddy",
        trace_id="trace-1",
        tenant_id="tenant-1",
        subject="issue-123",
        data={
            "reason": "Customer mapping is ambiguous",
            "capability": "finance.payment.execute",
        },
    )

    handler(event)

    items = list(approvals._items.values())
    assert len(items) == 1
    approval = items[0]
    assert approval.capability == "edi.operation.execute"
    assert approval.specialist_id == "eddy"
    assert approval.tenant_id == "tenant-1"
    assert approval.reason == "Customer mapping is ambiguous"


def test_unmapped_event_does_not_create_approval():
    approvals = InMemoryApprovalStore()
    handler = ApprovalEventHandler(approvals)
    event = IntelligenceEvent.create(
        event_type="edi.status.changed",
        source="eddy",
        trace_id="trace-2",
        tenant_id="tenant-1",
    )

    handler(event)

    assert approvals._items == {}
