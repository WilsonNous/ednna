from ednna.orchestration.contracts import IntelligenceRequest
from ednna.specialists.http_client import HttpSpecialistClient, SpecialistTransportError
from ednna.specialists.protocol import (
    CONTRACT_VERSION,
    CONTRACT_VERSION_HEADER,
    UnsupportedContractVersionError,
)

import pytest


class FakeResponse:
    def __init__(self, payload=None, error=None, headers=None):
        self._payload = payload or {}
        self._error = error
        self.headers = headers or {}

    def raise_for_status(self):
        if self._error:
            raise self._error

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, json, headers, timeout):
        self.calls.append(
            {
                "method": "POST",
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return self.response

    def get(self, url, headers, timeout):
        self.calls.append(
            {
                "method": "GET",
                "url": url,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return self.response


def test_query_uses_structured_versioned_contract_and_trace_header():
    session = FakeSession(
        FakeResponse(
            {
                "contract_version": CONTRACT_VERSION,
                "specialist_id": "eddy",
                "capability": "edi.status.get",
                "status": "success",
                "output": {"healthy": True},
                "confidence": 0.99,
                "evidence": [{"type": "operation", "id": "1"}],
                "trace_id": "trace-123",
            },
            headers={CONTRACT_VERSION_HEADER: CONTRACT_VERSION},
        )
    )
    client = HttpSpecialistClient(
        specialist_id="eddy",
        base_url="https://eddy.internal",
        api_token="token",
        timeout_seconds=5,
        session=session,
    )

    response = client.query(
        IntelligenceRequest(
            capability="edi.status.get",
            input={},
            user_id="99",
            tenant_id="netunna",
            trace_id="trace-123",
        )
    )

    call = session.calls[0]
    assert call["url"] == "https://eddy.internal/api/intelligence/query"
    assert call["headers"]["Authorization"] == "Bearer token"
    assert call["headers"]["X-Trace-Id"] == "trace-123"
    assert call["headers"][CONTRACT_VERSION_HEADER] == CONTRACT_VERSION
    assert call["json"]["contract_version"] == CONTRACT_VERSION
    assert call["timeout"] == 5
    assert response.output == {"healthy": True}
    assert response.confidence == 0.99


def test_explicit_incompatible_specialist_contract_version_is_rejected():
    session = FakeSession(
        FakeResponse(
            {
                "contract_version": "2",
                "specialist_id": "eddy",
                "capability": "edi.status.get",
                "status": "success",
                "output": {},
            }
        )
    )
    client = HttpSpecialistClient(
        specialist_id="eddy",
        base_url="https://eddy.internal",
        api_token="token",
        session=session,
    )

    with pytest.raises(UnsupportedContractVersionError):
        client.query(IntelligenceRequest(capability="edi.status.get", input={}))


def test_transport_error_does_not_expose_secret():
    class BrokenSession:
        def post(self, *args, **kwargs):
            import requests

            raise requests.ConnectionError("down")

    client = HttpSpecialistClient(
        specialist_id="eddy",
        base_url="https://eddy.internal",
        api_token="super-secret-token",
        session=BrokenSession(),
    )

    with pytest.raises(SpecialistTransportError) as exc:
        client.query(IntelligenceRequest(capability="edi.status.get", input={}))

    assert "super-secret-token" not in str(exc.value)


def test_action_status_lookup_is_read_only_and_versioned():
    session = FakeSession(
        FakeResponse(
            {
                "contract_version": CONTRACT_VERSION,
                "specialist_id": "eddy",
                "idempotency_key": "action-key-1",
                "state": "succeeded",
                "trace_id": "trace-123",
                "evidence": [{"type": "receipt", "id": "r-1"}],
                "reference": "eddy:r-1",
            },
            headers={CONTRACT_VERSION_HEADER: CONTRACT_VERSION},
        )
    )
    client = HttpSpecialistClient(
        specialist_id="eddy",
        base_url="https://eddy.internal",
        api_token="token",
        timeout_seconds=5,
        session=session,
    )

    status = client.action_status("action-key-1", "trace-123")

    call = session.calls[0]
    assert call["method"] == "GET"
    assert call["url"] == "https://eddy.internal/api/intelligence/actions/action-key-1"
    assert call["headers"]["X-Trace-Id"] == "trace-123"
    assert call["headers"][CONTRACT_VERSION_HEADER] == CONTRACT_VERSION
    assert status.state.value == "succeeded"
    assert status.reference == "eddy:r-1"
    assert status.evidence[0]["id"] == "r-1"


def test_action_status_rejects_mismatched_action_identity():
    session = FakeSession(
        FakeResponse(
            {
                "contract_version": CONTRACT_VERSION,
                "specialist_id": "eddy",
                "idempotency_key": "another-action",
                "state": "succeeded",
            },
            headers={CONTRACT_VERSION_HEADER: CONTRACT_VERSION},
        )
    )
    client = HttpSpecialistClient(
        specialist_id="eddy",
        base_url="https://eddy.internal",
        api_token="token",
        session=session,
    )

    with pytest.raises(SpecialistTransportError):
        client.action_status("action-key-1", "trace-123")
