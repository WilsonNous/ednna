from flask import Flask

from ednna.api.eddy_query import create_eddy_query_blueprint


def build_test_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(create_eddy_query_blueprint())
    return app


def test_eddy_query_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("EDDY_ENABLED", raising=False)
    client = build_test_app().test_client()

    response = client.post(
        "/api/eddy/query",
        json={"capability": "edi.status.get", "input": {}},
    )

    assert response.status_code == 503


def test_eddy_query_rejects_non_edi_capability(monkeypatch):
    monkeypatch.setenv("EDDY_ENABLED", "true")
    client = build_test_app().test_client()

    response = client.post(
        "/api/eddy/query",
        json={"capability": "finance.status.get", "input": {}},
    )

    assert response.status_code == 400
