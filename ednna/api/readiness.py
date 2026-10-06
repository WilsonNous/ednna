from __future__ import annotations

from flask import Blueprint, jsonify

from ednna.observability.readiness import ReadinessChecker


def create_readiness_blueprint() -> Blueprint:
    blueprint = Blueprint("readiness_api", __name__, url_prefix="/api")

    @blueprint.get("/readiness")
    def readiness():
        report = ReadinessChecker().check()
        payload = {
            "ready": report.ready,
            "checks": [
                {
                    "component": check.component,
                    "ready": check.ready,
                    "reason": None if check.ready else "configuration_missing",
                }
                for check in report.checks
            ],
        }
        return jsonify(payload), 200 if report.ready else 503

    return blueprint
