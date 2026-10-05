import pytest

from ednna.settings import AppSettings


REQUIRED_ENV = {
    "DB_HOST": "db.local",
    "DB_USER": "ednna",
    "DB_PASSWORD": "secret",
    "DB_NAME": "ednna",
    "SECRET_KEY": "session-secret",
    "ADMIN_PASSWORD": "admin-secret",
}


def test_settings_load_from_environment(monkeypatch):
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("DB_PORT", "3307")

    settings = AppSettings.from_env()

    assert settings.database.host == "db.local"
    assert settings.database.port == 3307
    assert settings.security.secret_key == "session-secret"


def test_settings_fail_fast_when_required_value_is_missing(monkeypatch):
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(RuntimeError):
        AppSettings.from_env()
