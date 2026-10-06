from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ednna.governance.action_control import ActionAuthorization, ActionAuthorizer
from ednna.governance.action_ledger import (
    ActionExecutionLedger,
    ActionExecutionNotReconcilableError,
    ActionExecutionStatus,
)
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
    ledger: ActionExecutionLedger | None = None,
) -> Blueprint:
    blueprint = Blueprint("action_api", __name__, url_prefix="/api/actions")
    authorization = AuthorizationService()
    authenticated = require_auth(authenticator)
    authorizer = ActionAuthorizer(build_action_policies(), approvals)
    controlled = ControlledActionService(gateway, authorizer, idempotency, ledger)

    @blueprint.get("/executions/<path:idempotency_key>")
    @authenticated
    def get_action_execution(idempotency_key: str):
        principal = g.principal

        try:
            authorization.require(principal, "ednna.actions:read")
        except AuthorizationDeniedError:
            return jsonify({"error": "forbidden"}), 403

        if ledger is None:
            return jsonify({"error": "action ledger unavailable"}), 503

        try:
            record = ledger.get(idempotency_key)
        except Exception:
            return jsonify({"error": "action ledger lookup failed"}), 502

        if record is None or record.tenant_id != principal.tenant_id:
            return jsonify({"error": "not found"}), 404

        return jsonify(
            {
                "idempotency_key": record.idempotency_key,
                "trace_id": record.trace_id,
                "capability": record.capability,
                "status": record.status.value,
                "started_at": record.started_at.isoformat(),
                "completed_at": (
                    record.completed_at.isoformat()
                    if record.completed_at
                    else None
                ),
                "specialist_id": record.specialist_id,
                "response_status": record.response_status,
                "evidence_count": record.evidence_count,
                "error_type": record.error_type,
                "reconciled_at": (
                    record.reconciled_at.isoformat()
                    if record.reconciled_at
                    else None
                ),
                "reconciled_by": record.reconciled_by,
                "reconciliation_reference": record.reconciliation_reference,
            }
        )

    @blueprint.get("/executions/<path:idempotency_key>/specialist-status")
    @authenticated
    def get_specialist_action_status(idempotency_key: str):
        principal = g.principal

        try:
            authorization.require(principal, "ednna.actions:read")
        except AuthorizationDeniedError:
            return jsonify({"error": "forbidden"}), 403

        if ledger is None:
            return jsonify({"error": "action ledger unavailable"}), 503

        try:
            current = ledger.get(idempotency_key)
        except Exception:
            return jsonify({"error": "action ledger lookup failed"}), 502

        if current is None or current.tenant_id != principal.tenant_id:
            return jsonify({"error": "not found"}), 404

        if current.status is not ActionExecutionStatus.UNCERTAIN:
            return jsonify({"error": "action execution is not uncertain"}), 409

        try:
            specialist_status = gateway.lookup_action_status(
                current.capability,
                idempotency_key,
                current.trace_id,
            )
        except Exception:
            return jsonify({"error": "specialist status lookup failed"}), 502

        return jsonify(
            {
                "idempotency_key": specialist_status.idempotency_key,
                "specialist_id": specialist_status.specialist_id,
                "state": specialist_status.state.value,
                "trace_id": specialist_status.trace_id,
                "evidence": list(specialist_status.evidence),
                "reference": specialist_status.reference,
                "ledger_status": current.status.value,
            }
        )

    @blueprint.post("/executions/<path:idempotency_key>/reconcile")
    @authenticated
    def reconcile_action_execution(idempotency_key: str):
        principal = g.principal

        try:
            authorization.require(principal, "ednna.actions:reconcile")
        except AuthorizationDeniedError:
            return jsonify({"error": "forbidden"}), 403

        if ledger is None:
            return jsonify({"error": "action ledger unavailable"}), 503

        try:
            current = ledger.get(idempotency_key)
        except Exception:
            return jsonify({"error": "action ledger lookup failed"}), 502

        if current is None or current.tenant_id != principal.tenant_id:
            return jsonify({"error": "not found"}), 404

        payload = request.get_json(silent=True) or {}
        decision = str(payload.get("decision", "")).strip()
        note = str(payload.get("note", "")).strip()
        reference = str(payload.get("reference", "")).strip()

        status_by_decision = {
            "confirmed_succeeded": ActionExecutionStatus.RECONCILED_SUCCEEDED,
            "confirmed_not_executed": ActionExecutionStatus.RECONCILED_NOT_EXECUTED,
        }
        target_status = status_by_decision.get(decision)

        if target_status is None:
            return jsonify({"error": "invalid reconciliation decision"}), 400
        if not note or not reference:
            return jsonify({"error": "note and reference are required"}), 400

        try:
            reconciled = ledger.reconcile(
                idempotency_key,
                target_status,
                reconciled_by=principal.user_id,
                note=note,
                reference=reference,
            )
        except ActionExecutionNotReconcilableError:
            return jsonify({"error": "action execution is not reconcilable"}), 409
        except Exception:
            return jsonify({"error": "action reconciliation failed"}), 502

        return jsonify(
            {
                "idempotency_key": reconciled.idempotency_key,
                "trace_id": reconciled.trace_id,
                "status": reconciled.status.value,
                "reconciled_at": (
                    reconciled.reconciled_at.isoformat()
                    if reconciled.reconciled_at
                    else None
                ),
                "reconciled_by": reconciled.reconciled_by,
                "reconciliation_reference": reconciled.reconciliation_reference,
            }
        )

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
