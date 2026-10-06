from ednna.specialists.http_client import HttpSpecialistClient
from ednna.specialists.protocol import CONTRACT_VERSION, CONTRACT_VERSION_HEADER


class FakeResponse:
    def __init__(self, payload, headers=None):
        self._payload = payload
        self.headers = headers or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, headers, timeout):
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return self.response


def test_http_handshake_returns_remote_identity_and_capabilities():
    session = FakeSession(
        FakeResponse(
            {
                "specialist_id": "eddy",
                "contract_version": CONTRACT_VERSION,
                "capabilities": ["edi.status.get", "edi.issue.inspect"],
                "status": "ready",
            },
            headers={CONTRACT_VERSION_HEADER: CONTRACT_VERSION},
        )
    )
    client = HttpSpecialistClient(
        specialist_id="eddy",
        base_url="https://eddy.internal",
        api_token="token",
        timeout_seconds=4,
        session=session,
    )

    handshake = client.handshake()

    assert handshake.specialist_id == "eddy"
    assert handshake.contract_version == CONTRACT_VERSION
    assert handshake.status == "ready"
    assert handshake.capabilities == ("edi.status.get", "edi.issue.inspect")
    call = session.calls[0]
    assert call["url"] == "https://eddy.internal/api/intelligence/handshake"
    assert call["headers"][CONTRACT_VERSION_HEADER] == CONTRACT_VERSION
    assert call["timeout"] == 4
