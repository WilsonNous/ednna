from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ednna.identity.authorization import AuthorizationDeniedError, AuthorizationService
from ednna.identity.flask_auth import require_auth
from ednna.identity.oidc import OIDCAuthenticator
from ednna.orchestration.discovery import CapabilityDiscovery
from ednna.orchestration.executor import ExecutionContext, PlanExecutor
from ednna.orchestration.gateway import IntelligenceGateway
from ednna.orchestration.planner import Planner
from ednna.orchestration.registry import SpecialistRegistry
from ednna.orchestration.presentation import ExecutivePresenter
from ednna.orchestration.service import OrchestrationService
from ednna.orchestration.synthesis import DeterministicSynthesizer
from ednna.specialists.availability import SpecialistAvailabilityRegistry


def create_multiagent_query_blueprint(
    authenticator: OIDCAuthenticator,
    registry: SpecialistRegistry,
    gateway: IntelligenceGateway,
    availability: SpecialistAvailabilityRegistry | None = None,
) -> Blueprint:
    blueprint = Blueprint("multiagent_query_api", __name__, url_prefix="/api/orchestration")
    authenticated = require_auth(authenticator)
    authorization = AuthorizationService()
    planner = Planner(CapabilityDiscovery(registry, availability=availability))
    executor = PlanExecutor(planner, OrchestrationService(gateway))
    synthesizer = DeterministicSynthesizer()
    presenter = ExecutivePresenter()

    @blueprint.post("/query")
    @authenticated
    def query():
        principal = g.principal
        payload = request.get_json(silent=True) or {}
        goal = str(payload.get("goal", "")).strip()
        action_input = payload.get("input", {})

        if not goal:
            return jsonify({"error": "goal is required"}), 400
        if not isinstance(action_input, dict):
            return jsonify({"error": "input must be an object"}), 400

        plan = planner.plan(goal)

        try:
            for step in plan.steps:
                authorization.require_query(principal, step.capability)
        except AuthorizationDeniedError:
            return jsonify({"error": "forbidden"}), 403

        try:
            execution = executor.execute_plan(
                plan,
                input=action_input,
                context=ExecutionContext(
                    user_id=principal.user_id,
                    tenant_id=principal.tenant_id,
                    conversation_id=payload.get("conversation_id"),
                ),
            )
        except Exception:
            return jsonify({"error": "multiagent query failed"}), 502

        synthesis = synthesizer.synthesize(execution)
        executive = presenter.present(synthesis)
        return jsonify(
            {
                "trace_id": synthesis.trace_id,
                "summary": executive.summary,
                "sections": [
                    {
                        "title": section.title,
                        "items": list(section.items),
                    }
                    for section in executive.sections
                ],
                "plan": [
                    {
                        "specialist_id": step.specialist_id,
                        "capability": step.capability,
                        "operation": step.operation.value,
                        "score": step.score,
                    }
                    for step in execution.plan.steps
                ],
                "findings": [
                    {
                        "specialist_id": finding.specialist_id,
                        "capability": finding.capability,
                        "status": finding.status,
                        "output": finding.output,
                        "confidence": finding.confidence,
                        "evidence": list(finding.evidence),
                        "warnings": list(finding.warnings),
                        "requires_human": finding.requires_human,
                    }
                    for finding in synthesis.findings
                ],
                "minimum_confidence": synthesis.minimum_confidence,
                "requires_human": synthesis.requires_human,
                "warnings": list(synthesis.warnings),
            }
        )

    return blueprint
