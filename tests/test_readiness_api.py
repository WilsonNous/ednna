from flask import Flask

from ednna.api.readiness import create_readiness_blueprint


def test_readiness_api_returns_503_when_required_base_config_is_missing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    app = Flask(__name__)
    app.register_blueprint(create_readiness_blueprint())
    response = app.test_client().get("/api/readiness")

    assert response.status_code == 503
    payload = response.get_json()
    assert payload["ready"] is False
    assert payload["checks"][0]["component"] == "application"


def test_readiness_api_does_not_expose_variable_names(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    app = Flask(__name__)
    app.register_blueprint(create_readiness_blueprint())
    response = app.test_client().get("/api/readiness")

    payload = response.get_json()
    serialized = str(payload)
    assert "SECRET_KEY" not in serialized
    assert "ADMIN_PASSWORD" not in serialized
    assert payload["checks"][0]["reason"] == "configuration_missing"
