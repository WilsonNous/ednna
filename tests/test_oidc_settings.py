import pytest

from ednna.settings import OIDCAppSettings


def test_oidc_settings_load_required_values(monkeypatch):
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example/")
    monkeypatch.setenv("OIDC_AUDIENCE", "api://ednna")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://issuer.example/keys")

    settings = OIDCAppSettings.from_env()

    assert settings.issuer == "https://issuer.example/"
    assert settings.audience == "api://ednna"
    assert settings.jwks_url == "https://issuer.example/keys"
    assert settings.user_claim == "oid"


def test_oidc_settings_fail_closed_when_missing(monkeypatch):
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    monkeypatch.setenv("OIDC_AUDIENCE", "api://ednna")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://issuer.example/keys")

    with pytest.raises(RuntimeError):
        OIDCAppSettings.from_env()
