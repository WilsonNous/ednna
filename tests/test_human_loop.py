from ednna.governance.approvals import ApprovalStatus, InMemoryApprovalStore
from ednna.governance.human_loop import HumanDecisionService
from ednna.orchestration.contracts import IntelligenceResponse


def test_requires_human_creates_pending_approval():
    store = InMemoryApprovalStore()
    service = HumanDecisionService(store)
    response = IntelligenceResponse(
        specialist_id="eddy",
        capability="edi.issue.inspect",
        status="blocked",
        output={},
        warnings=("Ambiguous customer mapping",),
        requires_human=True,
        trace_id="trace-approval",
    )

    approval = service.create_from_response(response)

    assert approval is not None
    assert approval.status is ApprovalStatus.PENDING
    assert approval.trace_id == "trace-approval"
    assert approval.reason == "Ambiguous customer mapping"


def test_human_decision_updates_state_and_actor():
    store = InMemoryApprovalStore()
    service = HumanDecisionService(store)
    response = IntelligenceResponse(
        specialist_id="eddy",
        capability="edi.issue.inspect",
        status="blocked",
        output={},
        requires_human=True,
        trace_id="trace-approval",
    )
    approval = service.create_from_response(response)
    assert approval is not None

    decided = service.decide(
        approval.approval_id,
        approved=True,
        decided_by="wilson",
        note="Validado manualmente",
    )

    assert decided.status is ApprovalStatus.APPROVED
    assert decided.decided_by == "wilson"
    assert decided.decided_at is not None


def test_non_human_response_does_not_create_approval():
    service = HumanDecisionService(InMemoryApprovalStore())
    response = IntelligenceResponse(
        specialist_id="eddy",
        capability="edi.status.get",
        status="success",
        output={},
        requires_human=False,
        trace_id="trace-ok",
    )

    assert service.create_from_response(response) is None
