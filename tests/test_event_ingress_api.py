from flask import Flask

from ednna.api.events import create_event_ingress_blueprint
from ednna.events.router import EventRouter
from ednna.events.service import EventService
from ednna.events.store import InMemoryEventStore
from ednna.identity.oidc import OIDCAuthenticator
from ednna.identity.principal import Principal


class FakeAuthenticator(OIDCAuthenticator):
    def __init__(self, principal):
        self._principal = principal

    def authenticate(self, token: str):
        return self._principal


def build_client(service_id="eddy-service", permissions=("ednna.events:publish",)):
    principal = Principal(
        user_id="service-user",
        tenant_id="tenant-1",
        service_id=service_id,
        permissions=tuple(permissions),
    )
    store = InMemoryEventStore()
    router = EventRouter()
    app = Flask(__name__)
    app.register_blueprint(
        create_event_ingress_blueprint(
            FakeAuthenticator(principal),
            EventService(store, router),
        )
    )
    return app.test_client(), store


def headers():
    return {"Authorization": "Bearer valid"}


def test_event_ingress_requires_service_identity():
    client, _ = build_client(service_id=None)

    response = client.post(
        "/api/events",
        headers=headers(),
        json={
            "event_id": "event-1",
            "event_type": "edi.issue.blocked",
            "trace_id": "trace-1",
            "data": {},
        },
    )

    assert response.status_code == 403


def test_event_ingress_uses_authenticated_service_and_tenant():
    client, store = build_client()

    response = client.post(
        "/api/events",
        headers=headers(),
        json={
            "event_id": "event-1",
            "event_type": "edi.issue.blocked",
            "trace_id": "trace-1",
            "source": "spoofed-source",
            "tenant_id": "spoofed-tenant",
            "data": {"issue_id": 123},
        },
    )

    assert response.status_code == 202
    event = store.list_by_trace("trace-1")[0]
    assert event.source == "eddy-service"
    assert event.tenant_id == "tenant-1"


def test_event_ingress_requires_publish_permission():
    client, _ = build_client(permissions=())

    response = client.post(
        "/api/events",
        headers=headers(),
        json={
            "event_id": "event-1",
            "event_type": "edi.issue.blocked",
            "trace_id": "trace-1",
            "data": {},
        },
    )

    assert response.status_code == 403
