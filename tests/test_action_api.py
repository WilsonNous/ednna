from datetime import datetime, timezone

from flask import Flask

from ednna.api.actions import create_action_blueprint
from ednna.governance.approvals import (
    ApprovalRequest,
    ApprovalStatus,
    InMemoryApprovalStore,
)
from ednna.governance.idempotency import InMemoryIdempotencyStore
from ednna.identity.oidc import OIDCAuthenticator
from ednna.identity.principal import Principal
from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse
from ednna.orchestration.gateway import IntelligenceGateway
from ednna.orchestration.registry import SpecialistRegistry
from ednna.specialists.eddy import EDDY_DESCRIPTOR


class FakeAuthenticator(OIDCAuthenticator):
    def __init__(self, principal):
        self._principal = principal

    def authenticate(self, token: str):
        return self._principal


class FakeEddyClient:
    def query(self, request: IntelligenceRequest):
        raise AssertionError("query should not be used")

    def action(self, request: IntelligenceRequest):
        return IntelligenceResponse(
            specialist_id="eddy",
            capability=request.capability,
            status="success",
            output={"executed": True},
            trace_id=request.trace_id,
        )


def build_client(
    permissions=("edi.operation.execute:action",),
    tenant_id="tenant-1",
    approval_tenant="tenant-1",
):
    principal = Principal(
        user_id="operator-1",
        tenant_id=tenant_id,
        permissions=tuple(permissions),
    )
    approvals = InMemoryApprovalStore()
    approvals.save(
        ApprovalRequest(
            approval_id="approval-1",
            trace_id="trace-1",
            capability="edi.operation.execute",
            specialist_id="eddy",
            reason="Approved manually",
            tenant_id=approval_tenant,
            requested_by="requester-1",
            status=ApprovalStatus.APPROVED,
            requested_at=datetime.now(timezone.utc),
            decided_at=datetime.now(timezone.utc),
            decided_by="reviewer-1",
        )
    )
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    gateway = IntelligenceGateway(registry)
    gateway.register_client("eddy", FakeEddyClient())

    app = Flask(__name__)
    app.register_blueprint(
        create_action_blueprint(
            FakeAuthenticator(principal),
            gateway,
            approvals,
            InMemoryIdempotencyStore(),
        )
    )
    return app.test_client()


def headers():
    return {"Authorization": "Bearer valid"}


def test_action_requires_explicit_permission():
    client = build_client(permissions=())

    response = client.post(
        "/api/actions/edi/operation/execute",
        headers=headers(),
        json={
            "approval_id": "approval-1",
            "idempotency_key": "key-1",
            "input": {},
        },
    )

    assert response.status_code == 403


def test_action_requires_same_tenant_approval():
    client = build_client(approval_tenant="other-tenant")

    response = client.post(
        "/api/actions/edi/operation/execute",
        headers=headers(),
        json={
            "approval_id": "approval-1",
            "idempotency_key": "key-1",
            "input": {},
        },
    )

    assert response.status_code == 403


def test_action_executes_only_with_permission_approval_and_idempotency():
    client = build_client()

    response = client.post(
        "/api/actions/edi/operation/execute",
        headers=headers(),
        json={
            "approval_id": "approval-1",
            "idempotency_key": "key-1",
            "input": {"issue_id": 123},
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["trace_id"] == "trace-1"
