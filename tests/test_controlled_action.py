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
