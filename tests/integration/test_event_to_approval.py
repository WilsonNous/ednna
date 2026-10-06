from ednna.events.approval_handler import ApprovalEventHandler
from ednna.events.contracts import IntelligenceEvent
from ednna.events.router import EventRouter
from ednna.events.service import EventService
from ednna.events.store import InMemoryEventStore


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


def test_authenticated_specialist_event_can_only_request_mapped_human_approval():
    event_store = InMemoryEventStore()
    approvals = CaptureApprovalStore()
    router = EventRouter()
    router.subscribe(
        "edi.operation.approval_required",
        ApprovalEventHandler(approvals),
    )
    service = EventService(event_store, router)

    event = IntelligenceEvent.create(
        event_type="edi.operation.approval_required",
        source="eddy-service",
        trace_id="trace-event-1",
        tenant_id="tenant-1",
        subject="issue-789",
        data={
            "reason": "Ambiguous operation",
            "capability": "finance.payment.execute",
        },
    )

    handled = service.publish(event)

    assert handled == 1
    assert len(approvals.saved) == 1
    approval = approvals.saved[0]
    assert approval.capability == "edi.operation.execute"
    assert approval.trace_id == "trace-event-1"
    assert approval.tenant_id == "tenant-1"
