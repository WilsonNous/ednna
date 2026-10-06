from datetime import datetime, timezone

from ednna.governance.action_control import ActionAuthorization, ActionAuthorizer
from ednna.governance.approvals import (
    ApprovalRequest,
    ApprovalStatus,
    InMemoryApprovalStore,
)
from ednna.governance.idempotency import (
    DuplicateActionError,
    InMemoryIdempotencyStore,
)
from ednna.governance.policies import CapabilityPolicy, GovernancePolicyRegistry
from ednna.orchestration.contracts import (
    IntelligenceRequest,
    IntelligenceResponse,
)
from ednna.orchestration.controlled_action import ControlledActionService
from ednna.orchestration.discovery import CapabilityDiscovery
from ednna.orchestration.gateway import IntelligenceGateway
from ednna.orchestration.planner import Planner
from ednna.orchestration.registry import SpecialistRegistry
from ednna.orchestration.service import OrchestrationService
from ednna.specialists.eddy import EDDY_DESCRIPTOR


class FakeEddyClient:
    def __init__(self):
        self.queries = []
        self.actions = []

    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        self.queries.append(request)
        return IntelligenceResponse(
            specialist_id="eddy",
            capability=request.capability,
            status="success",
            output={"issue_id": 123, "state": "blocked"},
            confidence=0.94,
            warnings=("Human review required",),
            requires_human=True,
            trace_id=request.trace_id,
        )

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        self.actions.append(request)
        return IntelligenceResponse(
            specialist_id="eddy",
            capability=request.capability,
            status="success",
            output={"executed": True},
            confidence=1.0,
            trace_id=request.trace_id,
        )


def build_stack():
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    client = FakeEddyClient()
    gateway = IntelligenceGateway(registry)
    gateway.register_client("eddy", client)
    query_service = OrchestrationService(gateway)

    approvals = InMemoryApprovalStore()
    policies = GovernancePolicyRegistry()
    policies.register(
        CapabilityPolicy(
            capability="edi.operation.execute",
            allow_autonomous_action=False,
            requires_human_approval=True,
        )
    )
    authorizer = ActionAuthorizer(policies, approvals)
    controlled = ControlledActionService(
        gateway,
        authorizer,
        InMemoryIdempotencyStore(),
    )

    return registry, client, query_service, approvals, controlled


def test_query_to_human_approval_to_controlled_action_preserves_trace():
    registry, client, query_service, approvals, controlled = build_stack()
    planner = Planner(CapabilityDiscovery(registry))

    plan = planner.plan("consultar chamado EDI")
    assert plan.steps
    assert plan.steps[0].capability == "edi.issue.inspect"

    query_request = IntelligenceRequest(
        capability=plan.steps[0].capability,
        input={"issue_id": 123},
        user_id="operator-1",
        tenant_id="tenant-1",
        trace_id="trace-e2e-1",
    )
    query_response = query_service.query(query_request)

    assert query_response.requires_human is True
    assert query_response.trace_id == "trace-e2e-1"

    approval = ApprovalRequest(
        approval_id="approval-1",
        trace_id=query_response.trace_id,
        capability="edi.operation.execute",
        specialist_id="eddy",
        reason="Validated by operator",
        tenant_id="tenant-1",
        requested_by="operator-1",
        status=ApprovalStatus.APPROVED,
        requested_at=datetime.now(timezone.utc),
        decided_at=datetime.now(timezone.utc),
        decided_by="reviewer-1",
    )
    approvals.save(approval)

    action_response = controlled.execute(
        IntelligenceRequest(
            capability="edi.operation.execute",
            input={"issue_id": 123},
            user_id="operator-1",
            tenant_id="tenant-1",
            trace_id=query_response.trace_id,
        ),
        ActionAuthorization(
            capability="edi.operation.execute",
            idempotency_key="issue-123-execute-v1",
            approval_id=approval.approval_id,
        ),
    )

    assert action_response.status == "success"
    assert action_response.trace_id == "trace-e2e-1"
    assert len(client.queries) == 1
    assert len(client.actions) == 1
    assert client.actions[0].trace_id == client.queries[0].trace_id


def test_same_action_cannot_execute_twice_with_same_idempotency_key():
    _, client, _, approvals, controlled = build_stack()
    approval = ApprovalRequest(
        approval_id="approval-2",
        trace_id="trace-e2e-2",
        capability="edi.operation.execute",
        specialist_id="eddy",
        reason="Approved",
        tenant_id="tenant-1",
        requested_by="operator-1",
        status=ApprovalStatus.APPROVED,
        requested_at=datetime.now(timezone.utc),
        decided_at=datetime.now(timezone.utc),
        decided_by="reviewer-1",
    )
    approvals.save(approval)

    request = IntelligenceRequest(
        capability="edi.operation.execute",
        input={"issue_id": 456},
        user_id="operator-1",
        tenant_id="tenant-1",
        trace_id="trace-e2e-2",
    )
    authorization = ActionAuthorization(
        capability="edi.operation.execute",
        idempotency_key="issue-456-execute-v1",
        approval_id=approval.approval_id,
    )

    controlled.execute(request, authorization)

    try:
        controlled.execute(request, authorization)
        raised = False
    except DuplicateActionError:
        raised = True

    assert raised is True
    assert len(client.actions) == 1
