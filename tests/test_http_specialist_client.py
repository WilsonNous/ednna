from ednna.orchestration.contracts import IntelligenceRequest
from ednna.specialists.http_client import HttpSpecialistClient, SpecialistTransportError

import pytest


class FakeResponse:
    def __init__(self, payload=None, error=None):
        self._payload = payload or {}
        self._error = error

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
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return self.response


def test_query_uses_structured_contract_and_trace_header():
    session = FakeSession(
        FakeResponse(
            {
                "specialist_id": "eddy",
                "capability": "edi.status.get",
                "status": "success",
                "output": {"healthy": True},
                "confidence": 0.99,
                "evidence": [{"type": "operation", "id": "1"}],
                "trace_id": "trace-123",
            }
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
    assert call["timeout"] == 5
    assert response.output == {"healthy": True}
    assert response.confidence == 0.99


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
