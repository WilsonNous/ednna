from __future__ import annotations

from flask import Blueprint, jsonify, request

from ednna.audit.recorder import AuditRecorder
from ednna.audit.store import InMemoryAuditStore
from ednna.bootstrap import build_eddy_gateway
from ednna.orchestration.audited_service import AuditedOrchestrationService
from ednna.orchestration.contracts import IntelligenceRequest
from ednna.orchestration.service import OrchestrationService
from ednna.specialists.feature_flags import eddy_enabled


def create_eddy_query_blueprint() -> Blueprint:
    blueprint = Blueprint("eddy_query_api", __name__, url_prefix="/api/eddy")
    audit_store = InMemoryAuditStore()

    @blueprint.post("/query")
    def query_eddy():
        if not eddy_enabled():
            return jsonify({"error": "EDDY integration is disabled"}), 503

        payload = request.get_json(silent=True) or {}
        capability = str(payload.get("capability", "")).strip()
        if not capability:
            return jsonify({"error": "capability is required"}), 400
        if not capability.startswith("edi."):
            return jsonify({"error": "only EDI query capabilities are accepted here"}), 400

        request_data = IntelligenceRequest(
            capability=capability,
            input=payload.get("input", {}),
            user_id=payload.get("user_id"),
            tenant_id=payload.get("tenant_id"),
            conversation_id=payload.get("conversation_id"),
            trace_id=payload.get("trace_id"),
        )

        service = OrchestrationService(build_eddy_gateway())
        audited = AuditedOrchestrationService(service, AuditRecorder(audit_store))

        try:
            response = audited.query(request_data)
        except Exception:
            return jsonify({"error": "EDDY query failed"}), 502

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
