from flask import Flask

from ednna.api.orchestration import create_orchestration_blueprint


def build_test_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(create_orchestration_blueprint())
    return app


def test_capability_catalog_exposes_eddy_without_internal_data():
    client = build_test_app().test_client()

    response = client.get("/api/orchestration/capabilities")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["specialists"][0]["specialist_id"] == "eddy"
    capability_names = {
        item["name"] for item in payload["specialists"][0]["capabilities"]
    }
    assert "edi.status.get" in capability_names


def test_plan_preview_returns_structured_steps_without_execution():
    client = build_test_app().test_client()

    response = client.post(
        "/api/orchestration/plan-preview",
        json={"goal": "qual o estado geral da operação EDI"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["steps"]
    assert payload["steps"][0]["capability"] == "edi.status.get"
    assert payload["steps"][0]["operation"] == "query"


def test_plan_preview_requires_goal():
    client = build_test_app().test_client()

    response = client.post("/api/orchestration/plan-preview", json={})

    assert response.status_code == 400
