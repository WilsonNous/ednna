from datetime import datetime, timezone

from flask import Flask

from ednna.api.approvals import create_approval_blueprint
from ednna.governance.approvals import ApprovalRequest, InMemoryApprovalStore
from ednna.identity.oidc import OIDCAuthenticator
from ednna.identity.principal import Principal


class FakeAuthenticator(OIDCAuthenticator):
    def __init__(self, principal):
        self._principal = principal

    def authenticate(self, token: str):
        if token != "valid":
            raise RuntimeError("unexpected token")
        return self._principal


def build_client(permissions=(), tenant_id="tenant-1"):
    store = InMemoryApprovalStore()
    approval = ApprovalRequest(
        approval_id="approval-1",
        trace_id="trace-1",
        capability="edi.operation.execute",
        specialist_id="eddy",
        reason="Manual validation",
        tenant_id="tenant-1",
        requested_by="requester-1",
        requested_at=datetime.now(timezone.utc),
    )
    store.save(approval)
    principal = Principal(
        user_id="reviewer-1",
        tenant_id=tenant_id,
        permissions=tuple(permissions),
    )
    app = Flask(__name__)
    app.register_blueprint(
        create_approval_blueprint(FakeAuthenticator(principal), store)
    )
    return app.test_client()


def auth_headers():
    return {"Authorization": "Bearer valid"}


def test_read_requires_permission():
    client = build_client()

    response = client.get("/api/approvals/approval-1", headers=auth_headers())

    assert response.status_code == 403


def test_read_is_tenant_scoped():
    client = build_client(
        permissions=("ednna.approvals:read",),
        tenant_id="other-tenant",
    )

    response = client.get("/api/approvals/approval-1", headers=auth_headers())

    assert response.status_code == 404


def test_decision_uses_authenticated_user():
    client = build_client(permissions=("ednna.approvals:decide",))

    response = client.post(
        "/api/approvals/approval-1/decision",
        headers=auth_headers(),
        json={"approved": True, "note": "Reviewed"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "approved"
    assert payload["decided_by"] == "reviewer-1"
