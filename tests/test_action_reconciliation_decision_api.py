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


def build_client(permissions=(), tenant_id="tenant-1"):
    principal = Principal(
        user_id="reviewer-1",
        tenant_id=tenant_id,
        permissions=tuple(permissions),
    )
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    ledger = InMemoryActionExecutionLedger()
    ledger.start(
        idempotency_key="action-key-1",
        trace_id="trace-1",
        capability="edi.operation.execute",
        tenant_id="tenant-1",
        requested_by="operator-1",
    )
    ledger.uncertain("action-key-1", "SpecialistTransportError")

    app = Flask(__name__)
    app.register_blueprint(
        create_action_blueprint(
            FakeAuthenticator(principal),
            IntelligenceGateway(registry),
            InMemoryApprovalStore(),
            InMemoryIdempotencyStore(),
            ledger,
        )
    )
    return app.test_client(), ledger


def headers():
    return {"Authorization": "Bearer valid"}


def test_reconciliation_requires_explicit_permission():
    client, _ledger = build_client()

    response = client.post(
        "/api/actions/executions/action-key-1/reconcile",
        headers=headers(),
        json={
            "decision": "confirmed_succeeded",
            "note": "Confirmed",
            "reference": "eddy:audit:1",
        },
    )

    assert response.status_code == 403


def test_reconciliation_requires_note_and_reference():
    client, _ledger = build_client(permissions=("ednna.actions:reconcile",))

    response = client.post(
        "/api/actions/executions/action-key-1/reconcile",
        headers=headers(),
        json={"decision": "confirmed_succeeded"},
    )

    assert response.status_code == 400


def test_uncertain_action_can_be_reconciled_without_retry():
    client, ledger = build_client(permissions=("ednna.actions:reconcile",))

    response = client.post(
        "/api/actions/executions/action-key-1/reconcile",
        headers=headers(),
        json={
            "decision": "confirmed_not_executed",
            "note": "No matching operation found in EDDY audit",
            "reference": "eddy:audit:missing:1",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "reconciled_not_executed"
    assert payload["reconciled_by"] == "reviewer-1"
    record = ledger.get("action-key-1")
    assert record is not None
    assert record.status.value == "reconciled_not_executed"


def test_reconciled_action_cannot_be_reconciled_again():
    client, _ledger = build_client(permissions=("ednna.actions:reconcile",))
    body = {
        "decision": "confirmed_succeeded",
        "note": "Confirmed",
        "reference": "eddy:audit:1",
    }

    first = client.post(
        "/api/actions/executions/action-key-1/reconcile",
        headers=headers(),
        json=body,
    )
    second = client.post(
        "/api/actions/executions/action-key-1/reconcile",
        headers=headers(),
        json=body,
    )

    assert first.status_code == 200
    assert second.status_code == 409
