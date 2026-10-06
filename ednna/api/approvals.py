from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ednna.governance.approvals import ApprovalStore
from ednna.governance.human_loop import ApprovalNotFoundError, HumanDecisionService
from ednna.identity.authorization import AuthorizationDeniedError, AuthorizationService
from ednna.identity.flask_auth import require_auth
from ednna.identity.oidc import OIDCAuthenticator


def create_approval_blueprint(
    authenticator: OIDCAuthenticator,
    store: ApprovalStore,
) -> Blueprint:
    blueprint = Blueprint("approval_api", __name__, url_prefix="/api/approvals")
    authorization = AuthorizationService()
    decisions = HumanDecisionService(store)
    authenticated = require_auth(authenticator)

    @blueprint.get("/<approval_id>")
    @authenticated
    def get_approval(approval_id: str):
        principal = g.principal
        try:
            authorization.require(principal, "ednna.approvals:read")
        except AuthorizationDeniedError:
            return jsonify({"error": "forbidden"}), 403

        approval = store.get(approval_id)
        if approval is None or approval.tenant_id != principal.tenant_id:
            return jsonify({"error": "not found"}), 404

        return jsonify(
            {
                "approval_id": approval.approval_id,
                "trace_id": approval.trace_id,
                "capability": approval.capability,
                "specialist_id": approval.specialist_id,
                "reason": approval.reason,
                "status": approval.status.value,
                "requested_at": approval.requested_at.isoformat(),
                "requested_by": approval.requested_by,
                "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
                "decided_by": approval.decided_by,
                "decision_note": approval.decision_note,
            }
        )

    @blueprint.post("/<approval_id>/decision")
    @authenticated
    def decide_approval(approval_id: str):
        principal = g.principal
        try:
            authorization.require(principal, "ednna.approvals:decide")
        except AuthorizationDeniedError:
            return jsonify({"error": "forbidden"}), 403

        current = store.get(approval_id)
        if current is None or current.tenant_id != principal.tenant_id:
            return jsonify({"error": "not found"}), 404

        payload = request.get_json(silent=True) or {}
        if "approved" not in payload or not isinstance(payload["approved"], bool):
            return jsonify({"error": "approved boolean is required"}), 400

        try:
            decided = decisions.decide(
                approval_id,
                approved=payload["approved"],
                decided_by=principal.user_id,
                note=payload.get("note"),
            )
        except ApprovalNotFoundError:
            return jsonify({"error": "not found"}), 404

        return jsonify(
            {
                "approval_id": decided.approval_id,
                "status": decided.status.value,
                "decided_by": decided.decided_by,
                "decided_at": decided.decided_at.isoformat() if decided.decided_at else None,
            }
        )

    return blueprint
