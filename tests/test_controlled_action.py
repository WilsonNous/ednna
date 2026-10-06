import pytest

from ednna.governance.action_control import (
    ActionAuthorization,
    ActionAuthorizer,
    HumanApprovalRequiredError,
    IdempotencyKeyRequiredError,
)
from ednna.governance.approvals import (
    ApprovalStatus,
    InMemoryApprovalStore,
    new_approval_request,
)
from ednna.governance.idempotency import (
    DuplicateActionError,
    InMemoryIdempotencyStore,
)
from ednna.governance.policies import CapabilityPolicy, GovernancePolicyRegistry


def build_authorizer():
    policies = GovernancePolicyRegistry()
    policies.register(
        CapabilityPolicy(
            capability="edi.operation.execute",
            allow_autonomous_action=False,
            requires_human_approval=True,
        )
    )
    approvals = InMemoryApprovalStore()
    return ActionAuthorizer(policies, approvals), approvals


def test_idempotency_key_is_mandatory():
    authorizer, _ = build_authorizer()

    with pytest.raises(IdempotencyKeyRequiredError):
        authorizer.authorize(
            ActionAuthorization(
                capability="edi.operation.execute",
                idempotency_key="",
            )
        )


def test_action_requires_approved_human_decision():
    authorizer, _ = build_authorizer()

    with pytest.raises(HumanApprovalRequiredError):
        authorizer.authorize(
            ActionAuthorization(
                capability="edi.operation.execute",
                idempotency_key="issue-123-action-1",
            )
        )


def test_matching_approved_decision_authorizes_action():
    authorizer, approvals = build_authorizer()
    approval = new_approval_request(
        trace_id="trace-1",
        capability="edi.operation.execute",
        specialist_id="eddy",
        reason="Manual approval required",
    )
    approvals.save(
        approval.__class__(
            approval_id=approval.approval_id,
            trace_id=approval.trace_id,
            capability=approval.capability,
            specialist_id=approval.specialist_id,
            reason=approval.reason,
            status=ApprovalStatus.APPROVED,
            requested_at=approval.requested_at,
            decided_by="wilson",
        )
    )

    authorizer.authorize(
        ActionAuthorization(
            capability="edi.operation.execute",
            idempotency_key="issue-123-action-1",
            approval_id=approval.approval_id,
        )
    )


def test_duplicate_idempotency_key_is_blocked():
    store = InMemoryIdempotencyStore()
    store.reserve("same-key")

    with pytest.raises(DuplicateActionError):
        store.reserve("same-key")


def test_controlled_service_rejects_capability_mismatch_before_dispatch():
    from ednna.orchestration.controlled_action import (
        ActionCapabilityMismatchError,
        ControlledActionService,
    )
    from ednna.orchestration.contracts import IntelligenceRequest
    from ednna.orchestration.gateway import IntelligenceGateway
    from ednna.orchestration.registry import SpecialistRegistry
    from ednna.specialists.eddy import EDDY_DESCRIPTOR

    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    gateway = IntelligenceGateway(registry)
    authorizer, _ = build_authorizer()
    service = ControlledActionService(
        gateway,
        authorizer,
        InMemoryIdempotencyStore(),
    )

    with pytest.raises(ActionCapabilityMismatchError):
        service.execute(
            IntelligenceRequest(
                capability="edi.operation.execute",
                input={},
            ),
            ActionAuthorization(
                capability="edi.status.get",
                idempotency_key="k1",
            ),
        )


def test_approval_binding_is_idempotent_for_same_action_key():
    authorizer, approvals = build_authorizer()
    approval = new_approval_request(
        trace_id="trace-bind-1",
        capability="edi.operation.execute",
        specialist_id="eddy",
        reason="Approved",
    )
    approved = approval.__class__(
        approval_id=approval.approval_id,
        trace_id=approval.trace_id,
        capability=approval.capability,
        specialist_id=approval.specialist_id,
        reason=approval.reason,
        status=ApprovalStatus.APPROVED,
        requested_at=approval.requested_at,
    )
    approvals.save(approved)

    authorization = ActionAuthorization(
        capability="edi.operation.execute",
        idempotency_key="action-key-1",
        approval_id=approval.approval_id,
    )

    authorizer.authorize(authorization)
    authorizer.bind(authorization)
    authorizer.authorize(authorization)
    authorizer.bind(authorization)

    bound = approvals.get(approval.approval_id)
    assert bound is not None
    assert bound.action_idempotency_key == "action-key-1"
    assert bound.action_bound_at is not None


def test_approval_cannot_be_reused_for_different_action_key():
    authorizer, approvals = build_authorizer()
    approval = new_approval_request(
        trace_id="trace-bind-2",
        capability="edi.operation.execute",
        specialist_id="eddy",
        reason="Approved",
    )
    approved = approval.__class__(
        approval_id=approval.approval_id,
        trace_id=approval.trace_id,
        capability=approval.capability,
        specialist_id=approval.specialist_id,
        reason=approval.reason,
        status=ApprovalStatus.APPROVED,
        requested_at=approval.requested_at,
    )
    approvals.save(approved)

    first = ActionAuthorization(
        capability="edi.operation.execute",
        idempotency_key="action-key-1",
        approval_id=approval.approval_id,
    )
    authorizer.authorize(first)
    authorizer.bind(first)

    with pytest.raises(HumanApprovalRequiredError):
        authorizer.authorize(
            ActionAuthorization(
                capability="edi.operation.execute",
                idempotency_key="action-key-2",
                approval_id=approval.approval_id,
            )
        )


def build_controlled_service_with_ledger(client, ledger):
    from ednna.governance.action_ledger import InMemoryActionExecutionLedger
    from ednna.orchestration.controlled_action import ControlledActionService
    from ednna.orchestration.gateway import IntelligenceGateway
    from ednna.orchestration.registry import SpecialistRegistry
    from ednna.specialists.eddy import EDDY_DESCRIPTOR

    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    gateway = IntelligenceGateway(registry)
    gateway.register_client("eddy", client)

    authorizer, approvals = build_authorizer()
    approval = new_approval_request(
        trace_id="trace-ledger",
        capability="edi.operation.execute",
        specialist_id="eddy",
        reason="Approved",
    )
    approved = approval.__class__(
        approval_id=approval.approval_id,
        trace_id=approval.trace_id,
        capability=approval.capability,
        specialist_id=approval.specialist_id,
        reason=approval.reason,
        status=ApprovalStatus.APPROVED,
        requested_at=approval.requested_at,
    )
    approvals.save(approved)

    service = ControlledActionService(
        gateway,
        authorizer,
        InMemoryIdempotencyStore(),
        ledger,
    )
    return service, approved


def test_controlled_action_marks_ledger_succeeded():
    from ednna.governance.action_ledger import (
        ActionExecutionStatus,
        InMemoryActionExecutionLedger,
    )
    from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse

    class SuccessClient:
        def query(self, request):
            raise AssertionError("query not expected")

        def action(self, request):
            return IntelligenceResponse(
                specialist_id="eddy",
                capability=request.capability,
                status="success",
                output={},
                evidence=({"type": "operation", "id": "op-1"},),
                trace_id=request.trace_id,
            )

    ledger = InMemoryActionExecutionLedger()
    service, approval = build_controlled_service_with_ledger(SuccessClient(), ledger)
    key = "ledger-success-1"

    response = service.execute(
        IntelligenceRequest(
            capability="edi.operation.execute",
            input={},
            user_id="operator-1",
            tenant_id="tenant-1",
            trace_id="trace-ledger",
        ),
        ActionAuthorization(
            capability="edi.operation.execute",
            idempotency_key=key,
            approval_id=approval.approval_id,
        ),
    )

    record = ledger.get(key)
    assert response.status == "success"
    assert record is not None
    assert record.status is ActionExecutionStatus.SUCCEEDED
    assert record.specialist_id == "eddy"
    assert record.evidence_count == 1


def test_controlled_action_marks_ledger_uncertain_after_dispatch_error():
    from ednna.governance.action_ledger import (
        ActionExecutionStatus,
        InMemoryActionExecutionLedger,
    )
    from ednna.orchestration.contracts import IntelligenceRequest
    from ednna.specialists.http_client import SpecialistTransportError

    class FailingClient:
        def query(self, request):
            raise AssertionError("query not expected")

        def action(self, request):
            raise SpecialistTransportError("remote result unknown")

    ledger = InMemoryActionExecutionLedger()
    service, approval = build_controlled_service_with_ledger(FailingClient(), ledger)
    key = "ledger-uncertain-1"

    with pytest.raises(SpecialistTransportError):
        service.execute(
            IntelligenceRequest(
                capability="edi.operation.execute",
                input={},
                trace_id="trace-ledger",
            ),
            ActionAuthorization(
                capability="edi.operation.execute",
                idempotency_key=key,
                approval_id=approval.approval_id,
            ),
        )

    record = ledger.get(key)
    assert record is not None
    assert record.status is ActionExecutionStatus.UNCERTAIN
    assert record.error_type == "SpecialistTransportError"


def test_action_is_not_dispatched_when_ledger_start_fails():
    from ednna.governance.action_ledger import DuplicateActionExecutionError
    from ednna.orchestration.contracts import IntelligenceRequest

    class CountingClient:
        def __init__(self):
            self.actions = 0

        def query(self, request):
            raise AssertionError("query not expected")

        def action(self, request):
            self.actions += 1
            raise AssertionError("dispatch must not occur")

    class FailingLedger:
        def start(self, **kwargs):
            raise DuplicateActionExecutionError("duplicate")

        def succeed(self, *args, **kwargs):
            raise AssertionError("not expected")

        def uncertain(self, *args, **kwargs):
            raise AssertionError("not expected")

    client = CountingClient()
    service, approval = build_controlled_service_with_ledger(client, FailingLedger())

    with pytest.raises(DuplicateActionExecutionError):
        service.execute(
            IntelligenceRequest(
                capability="edi.operation.execute",
                input={},
                trace_id="trace-ledger",
            ),
            ActionAuthorization(
                capability="edi.operation.execute",
                idempotency_key="ledger-start-fail",
                approval_id=approval.approval_id,
            ),
        )

    assert client.actions == 0
