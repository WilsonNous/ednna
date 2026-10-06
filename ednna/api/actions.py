from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ednna.governance.action_control import ActionAuthorization, ActionAuthorizer
from ednna.governance.approvals import (
    ApprovalAlreadyBoundError,
    ApprovalStatus,
    ApprovalStore,
)
from ednna.governance.action_execution import (
    ActionExecutionMode,
    action_execution_mode,
)
from ednna.governance.idempotency import DuplicateActionError, IdempotencyStore
from ednna.governance.policies import CapabilityPolicy, GovernancePolicyRegistry
from ednna.identity.authorization import AuthorizationDeniedError, AuthorizationService
from ednna.identity.flask_auth import require_auth
from ednna.identity.oidc import OIDCAuthenticator
from ednna.orchestration.contracts import IntelligenceRequest
from ednna.orchestration.controlled_action import ControlledActionService
from ednna.orchestration.gateway import IntelligenceGateway


def build_action_policies() -> GovernancePolicyRegistry:
    policies = GovernancePolicyRegistry()
    policies.register(
        CapabilityPolicy(
            capability="edi.operation.execute",
            allow_autonomous_action=False,
            requires_human_approval=True,
        )
    )
    return policies


def create_action_blueprint(
    authenticator: OIDCAuthenticator,
    gateway: IntelligenceGateway,
    approvals: ApprovalStore,
    idempotency: IdempotencyStore,
) -> Blueprint:
    blueprint = Blueprint("action_api", __name__, url_prefix="/api/actions")
    authorization = AuthorizationService()
    authenticated = require_auth(authenticator)
    authorizer = ActionAuthorizer(build_action_policies(), approvals)
    controlled = ControlledActionService(gateway, authorizer, idempotency)

    @blueprint.post("/edi/operation/execute")
    @authenticated
    def execute_edi_operation():
        principal = g.principal
        capability = "edi.operation.execute"

        try:
            authorization.require_action(principal, capability)
        except AuthorizationDeniedError:
            return jsonify({"error": "forbidden"}), 403

        payload = request.get_json(silent=True) or {}
        approval_id = str(payload.get("approval_id", "")).strip()
        idempotency_key = str(payload.get("idempotency_key", "")).strip()
        action_input = payload.get("input", {})

        if not approval_id:
            return jsonify({"error": "approval_id is required"}), 400
        if not idempotency_key:
            return jsonify({"error": "idempotency_key is required"}), 400
        if not isinstance(action_input, dict):
            return jsonify({"error": "input must be an object"}), 400

        approval = approvals.get(approval_id)
        if (
            approval is None
            or approval.status is not ApprovalStatus.APPROVED
            or approval.tenant_id != principal.tenant_id
            or approval.capability != capability
        ):
            return jsonify({"error": "valid approved decision is required"}), 403

        action_authorization = ActionAuthorization(
            capability=capability,
            idempotency_key=idempotency_key,
            approval_id=approval_id,
        )

        if action_execution_mode() is ActionExecutionMode.DRY_RUN:
            try:
                authorizer.authorize(action_authorization)
            except Exception:
                return jsonify({"error": "controlled action validation failed"}), 403

            return jsonify(
                {
                    "specialist_id": approval.specialist_id,
                    "capability": capability,
                    "status": "dry_run",
                    "output": {
                        "validated": True,
                        "executed": False,
                    },
                    "confidence": None,
                    "evidence": [],
                    "warnings": [],
                    "requires_human": False,
                    "trace_id": approval.trace_id,
                }
            )

        action_request = IntelligenceRequest(
            capability=capability,
            input=action_input,
            user_id=principal.user_id,
            tenant_id=principal.tenant_id,
            trace_id=approval.trace_id,
        )

        try:
            response = controlled.execute(
                action_request,
                action_authorization,
            )
        except ApprovalAlreadyBoundError:
            return jsonify({"error": "approval already bound to another action"}), 409
        except DuplicateActionError:
            return jsonify({"error": "duplicate action blocked"}), 409
        except Exception:
            return jsonify({"error": "controlled action failed"}), 502

        return jsonify(
            {
                "specialist_id": response.specialist_id,
                "capability": response.capability,
                "status": response.status,
                "output": response.output,
                "confidence": response.confidence,
                "evidence": list(response.evidence),
                "warnings": list(response.warnings),
                "requires_human": response.requires_human,
                "trace_id": response.trace_id,
            }
        )

    return blueprint
