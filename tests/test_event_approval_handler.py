from ednna.events.approval_handler import ApprovalEventHandler
from ednna.events.contracts import IntelligenceEvent


class CaptureApprovalStore:
    def __init__(self):
        self.saved = []

    def save(self, approval):
        self.saved.append(approval)

    def get(self, approval_id):
        return next(
            (item for item in self.saved if item.approval_id == approval_id),
            None,
        )


def test_mapped_event_creates_human_approval_for_fixed_capability():
    approvals = CaptureApprovalStore()
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

    assert len(approvals.saved) == 1
    approval = approvals.saved[0]
    assert approval.capability == "edi.operation.execute"
    assert approval.specialist_id == "eddy"
    assert approval.tenant_id == "tenant-1"
    assert approval.reason == "Customer mapping is ambiguous"


def test_unmapped_event_does_not_create_approval():
    approvals = CaptureApprovalStore()
    handler = ApprovalEventHandler(approvals)
    event = IntelligenceEvent.create(
        event_type="edi.status.changed",
        source="eddy",
        trace_id="trace-2",
        tenant_id="tenant-1",
    )

    handler(event)

    assert approvals.saved == []
