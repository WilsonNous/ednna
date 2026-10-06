from flask import Flask

from ednna.api.multiagent import create_multiagent_query_blueprint
from ednna.identity.oidc import OIDCAuthenticator
from ednna.identity.principal import Principal
from ednna.orchestration.contracts import (
    Capability,
    IntelligenceRequest,
    IntelligenceResponse,
    OperationKind,
    SpecialistDescriptor,
)
from ednna.orchestration.gateway import IntelligenceGateway
from ednna.orchestration.registry import SpecialistRegistry
from ednna.specialists.eddy import EDDY_DESCRIPTOR


class FakeAuthenticator(OIDCAuthenticator):
    def __init__(self, principal):
        self._principal = principal

    def authenticate(self, token: str):
        return self._principal


class FakeClient:
    def __init__(self, specialist_id):
        self.specialist_id = specialist_id

    def query(self, request: IntelligenceRequest):
        return IntelligenceResponse(
            specialist_id=self.specialist_id,
            capability=request.capability,
            status="success",
            output={"source": self.specialist_id},
            confidence=0.9,
            trace_id=request.trace_id,
        )

    def action(self, request: IntelligenceRequest):
        raise AssertionError("ACTION must not be used by multiagent query API")


def build_client(permissions):
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    registry.register(
        SpecialistDescriptor(
            specialist_id="finance",
            name="Finance",
            domain="finance",
            description="Especialista financeiro",
            capabilities=(
                Capability(
                    "finance.exposure.get",
                    OperationKind.QUERY,
                    "Consultar exposição financeira do cliente",
                ),
            ),
        )
    )
    gateway = IntelligenceGateway(registry)
    gateway.register_client("eddy", FakeClient("eddy"))
    gateway.register_client("finance", FakeClient("finance"))

    principal = Principal(
        user_id="user-1",
        tenant_id="tenant-1",
        permissions=tuple(permissions),
    )
    app = Flask(__name__)
    app.register_blueprint(
        create_multiagent_query_blueprint(
            FakeAuthenticator(principal),
            registry,
            gateway,
        )
    )
    return app.test_client()


def headers():
    return {"Authorization": "Bearer valid"}


def test_multiagent_query_requires_permission_for_every_planned_capability():
    client = build_client(permissions=("edi.status.get:query",))

    response = client.post(
        "/api/orchestration/query",
        headers=headers(),
        json={"goal": "consultar EDI e exposição financeira do cliente", "input": {}},
    )

    assert response.status_code == 403


def test_multiagent_query_combines_authorized_specialists():
    client = build_client(
        permissions=(
            "edi.status.get:query",
            "finance.exposure.get:query",
        )
    )

    response = client.post(
        "/api/orchestration/query",
        headers=headers(),
        json={"goal": "consultar EDI e exposição financeira do cliente", "input": {}},
    )

    assert response.status_code == 200
    payload = response.get_json()
    specialist_ids = {finding["specialist_id"] for finding in payload["findings"]}
    assert "eddy" in specialist_ids
    assert "finance" in specialist_ids
    assert all(step["operation"] == "query" for step in payload["plan"])
