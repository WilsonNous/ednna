import pytest

from ednna.identity.oidc import AuthenticationError, OIDCAuthenticator, OIDCSettings


class FakeSigningKey:
    key = "public-key"


class FakeJWKClient:
    def get_signing_key_from_jwt(self, token):
        assert token == "valid-token"
        return FakeSigningKey()


def test_authenticator_maps_verified_claims_to_principal(monkeypatch):
    settings = OIDCSettings(
        issuer="https://issuer.example/",
        audience="api://ednna",
        jwks_url="https://issuer.example/keys",
    )
    authenticator = OIDCAuthenticator(settings, jwk_client=FakeJWKClient())

    monkeypatch.setattr(
        "ednna.identity.oidc.jwt.decode",
        lambda *args, **kwargs: {
            "oid": "user-1",
            "tid": "tenant-1",
            "azp": "service-1",
            "roles": ["Admin"],
            "scp": "edi.status.get:query edi.operation.execute:action",
        },
    )

    principal = authenticator.authenticate("valid-token")

    assert principal.user_id == "user-1"
    assert principal.tenant_id == "tenant-1"
    assert principal.service_id == "service-1"
    assert "Admin" in principal.roles
    assert "edi.status.get:query" in principal.permissions


def test_authenticator_rejects_missing_identity_claims(monkeypatch):
    settings = OIDCSettings(
        issuer="https://issuer.example/",
        audience="api://ednna",
        jwks_url="https://issuer.example/keys",
    )
    authenticator = OIDCAuthenticator(settings, jwk_client=FakeJWKClient())

    monkeypatch.setattr(
        "ednna.identity.oidc.jwt.decode",
        lambda *args, **kwargs: {"tid": "tenant-1"},
    )

    with pytest.raises(AuthenticationError):
        authenticator.authenticate("valid-token")
