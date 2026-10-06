from flask import Flask

from ednna.api.actions import create_action_blueprint
from ednna.governance.action_ledger import InMemoryActionExecutionLedger
from ednna.governance.approvals import InMemoryApprovalStore
from ednna.governance.idempotency import InMemoryIdempotencyStore
from ednna.identity.oidc import OIDCAuthenticator
from ednna.identity.principal import Principal
from ednna.orchestration.gateway import IntelligenceGateway
from ednna.orchestration.registry import SpecialistRegistry
from ednna.specialists.action_status import SpecialistActionState, SpecialistActionStatus
from ednna.specialists.eddy import EDDY_DESCRIPTOR


class FakeAuthenticator(OIDCAuthenticator):
    def __init__(self, principal):
        self._principal = principal

    def authenticate(self, token: str):
        return self._principal


class StatusOnlyEddyClient:
    def __init__(self):
        self.action_calls = 0
        self.status_calls = 0

    def query(self, request):
        raise AssertionError("query must not be used")

    def action(self, request):
        self.action_calls += 1
        raise AssertionError("ACTION must never be replayed during reconciliation lookup")

    def action_status(self, idempotency_key: str, trace_id: str | None = None):
        self.status_calls += 1
        return SpecialistActionStatus(
            specialist_id="eddy",
            idempotency_key=idempotency_key,
            state=SpecialistActionState.SUCCEEDED,
            trace_id=trace_id,
            evidence=({"type": "remote_action_receipt", "id": "receipt-1"},),
            reference="eddy:receipt-1",
        )


def build_client(ledger_status_uncertain=True, tenant_id="tenant-1"):
    principal = Principal(
        user_id="reviewer-1",
        tenant_id=tenant_id,
        permissions=("ednna.actions:read",),
    )
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    gateway = IntelligenceGateway(registry)
    specialist = StatusOnlyEddyClient()
    gateway.register_client("eddy", specialist)

    ledger = InMemoryActionExecutionLedger()
    ledger.start(
        idempotency_key="action-key-1",
        trace_id="trace-1",
        capability="edi.operation.execute",
        tenant_id="tenant-1",
        requested_by="operator-1",
    )
    if ledger_status_uncertain:
        ledger.uncertain("action-key-1", "SpecialistTransportError")
    else:
        ledger.succeed("action-key-1", "eddy", "success", 1)

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
    return app.test_client(), specialist


def headers():
    return {"Authorization": "Bearer valid"}


def test_specialist_status_lookup_never_replays_action():
    client, specialist = build_client()

    response = client.get(
        "/api/actions/executions/action-key-1/specialist-status",
        headers=headers(),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["state"] == "succeeded"
    assert payload["ledger_status"] == "uncertain"
    assert payload["reference"] == "eddy:receipt-1"
    assert specialist.status_calls == 1
    assert specialist.action_calls == 0


def test_specialist_status_lookup_only_applies_to_uncertain_execution():
    client, specialist = build_client(ledger_status_uncertain=False)

    response = client.get(
        "/api/actions/executions/action-key-1/specialist-status",
        headers=headers(),
    )

    assert response.status_code == 409
    assert specialist.status_calls == 0
    assert specialist.action_calls == 0


def test_specialist_status_lookup_is_tenant_scoped():
    client, specialist = build_client(tenant_id="other-tenant")

    response = client.get(
        "/api/actions/executions/action-key-1/specialist-status",
        headers=headers(),
    )

    assert response.status_code == 404
    assert specialist.status_calls == 0
