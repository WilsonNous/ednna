from flask import Flask

from ednna.api.actions import create_action_blueprint
from ednna.governance.action_ledger import InMemoryActionExecutionLedger
from ednna.governance.approvals import InMemoryApprovalStore
from ednna.governance.idempotency import InMemoryIdempotencyStore
from ednna.identity.oidc import OIDCAuthenticator
from ednna.identity.principal import Principal
from ednna.orchestration.gateway import IntelligenceGateway
from ednna.orchestration.registry import SpecialistRegistry
from ednna.specialists.eddy import EDDY_DESCRIPTOR


class FakeAuthenticator(OIDCAuthenticator):
    def __init__(self, principal):
        self._principal = principal

    def authenticate(self, token: str):
        return self._principal


def build_client(permissions=(), tenant_id="tenant-1", record_tenant="tenant-1"):
    principal = Principal(
        user_id="reviewer-1",
        tenant_id=tenant_id,
        permissions=tuple(permissions),
    )

    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    gateway = IntelligenceGateway(registry)

    ledger = InMemoryActionExecutionLedger()
    ledger.start(
        idempotency_key="action-key-1",
        trace_id="trace-1",
        capability="edi.operation.execute",
        tenant_id=record_tenant,
        requested_by="operator-1",
    )
    ledger.uncertain("action-key-1", "SpecialistTransportError")

    app = Flask(__name__)
    app.register_blueprint(
        create_action_blueprint(
            FakeAuthenticator(principal),
            gateway,
            InMemoryApprovalStore(),
            InMemoryIdempotencyStore(),
            ledger,
        )
    )
    return app.test_client()


def headers():
    return {"Authorization": "Bearer valid"}


def test_action_execution_status_requires_read_permission():
    client = build_client()

    response = client.get(
        "/api/actions/executions/action-key-1",
        headers=headers(),
    )

    assert response.status_code == 403


def test_action_execution_status_is_tenant_scoped():
    client = build_client(
        permissions=("ednna.actions:read",),
        tenant_id="other-tenant",
    )

    response = client.get(
        "/api/actions/executions/action-key-1",
        headers=headers(),
    )

    assert response.status_code == 404


def test_action_execution_status_exposes_safe_reconciliation_state():
    client = build_client(permissions=("ednna.actions:read",))

    response = client.get(
        "/api/actions/executions/action-key-1",
        headers=headers(),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "uncertain"
    assert payload["trace_id"] == "trace-1"
    assert payload["capability"] == "edi.operation.execute"
    assert payload["error_type"] == "SpecialistTransportError"
    assert "input" not in payload
