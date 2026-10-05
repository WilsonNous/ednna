from __future__ import annotations

from flask import Blueprint, jsonify, request

from ednna.bootstrap import build_planner, build_registry


def create_orchestration_blueprint() -> Blueprint:
    blueprint = Blueprint("orchestration_api", __name__, url_prefix="/api/orchestration")
    registry = build_registry()
    planner = build_planner()

    @blueprint.get("/capabilities")
    def capabilities():
        specialists = []
        for specialist in registry.list_specialists():
            specialists.append(
                {
                    "specialist_id": specialist.specialist_id,
                    "name": specialist.name,
                    "domain": specialist.domain,
                    "description": specialist.description,
                    "capabilities": [
                        {
                            "name": capability.name,
                            "kind": capability.kind.value,
                            "description": capability.description,
                        }
                        for capability in specialist.capabilities
                    ],
                }
            )
        return jsonify({"specialists": specialists})

    @blueprint.post("/plan-preview")
    def plan_preview():
        payload = request.get_json(silent=True) or {}
        goal = str(payload.get("goal", "")).strip()
        if not goal:
            return jsonify({"error": "goal is required"}), 400

        plan = planner.plan(goal)
        return jsonify(
            {
                "goal": plan.goal,
                "steps": [
                    {
                        "specialist_id": step.specialist_id,
                        "capability": step.capability,
                        "operation": step.operation.value,
                        "score": step.score,
                    }
                    for step in plan.steps
                ],
            }
        )

    return blueprint
