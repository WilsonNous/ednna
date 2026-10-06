from flask import Flask

from ednna.api.runtime import create_runtime_blueprint


def test_runtime_reports_legacy_chat_by_default(monkeypatch):
    monkeypatch.delenv("ORCHESTRATED_CHAT_ENABLED", raising=False)
    monkeypatch.delenv("EDDY_ENABLED", raising=False)

    app = Flask(__name__)
    app.register_blueprint(create_runtime_blueprint())
    response = app.test_client().get("/api/runtime")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["platform"] == "EDNNA 2.0"
    assert payload["chat_mode"] == "legacy"
    assert payload["features"]["eddy"] is False
