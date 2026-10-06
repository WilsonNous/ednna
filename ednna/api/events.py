from __future__ import annotations

from datetime import datetime

from flask import Blueprint, g, jsonify, request

from ednna.events.contracts import IntelligenceEvent
from ednna.events.mysql_store import DuplicateEventError
from ednna.events.service import EventService
from ednna.identity.authorization import AuthorizationDeniedError, AuthorizationService
from ednna.identity.flask_auth import require_auth
from ednna.identity.oidc import OIDCAuthenticator


def create_event_ingress_blueprint(
    authenticator: OIDCAuthenticator,
    event_service: EventService,
) -> Blueprint:
    blueprint = Blueprint("event_ingress_api", __name__, url_prefix="/api/events")
    authenticated = require_auth(authenticator)
    authorization = AuthorizationService()

    @blueprint.post("")
    @authenticated
    def publish_event():
        principal = g.principal

        if not principal.service_id:
            return jsonify({"error": "service identity required"}), 403

        try:
            authorization.require(principal, "ednna.events:publish")
        except AuthorizationDeniedError:
            return jsonify({"error": "forbidden"}), 403

        payload = request.get_json(silent=True) or {}
        event_id = str(payload.get("event_id", "")).strip()
        event_type = str(payload.get("event_type", "")).strip()
        trace_id = str(payload.get("trace_id", "")).strip()
        subject = payload.get("subject")
        data = payload.get("data", {})
        occurred_at_raw = payload.get("occurred_at")

        if not event_id or not event_type or not trace_id:
            return jsonify({"error": "event_id, event_type and trace_id are required"}), 400
        if not isinstance(data, dict):
            return jsonify({"error": "data must be an object"}), 400

        occurred_at = None
        if occurred_at_raw:
            try:
                occurred_at = datetime.fromisoformat(
                    str(occurred_at_raw).replace("Z", "+00:00")
                )
            except ValueError:
                return jsonify({"error": "invalid occurred_at"}), 400

        event = IntelligenceEvent(
            event_id=event_id,
            event_type=event_type,
            source=principal.service_id,
            trace_id=trace_id,
            tenant_id=principal.tenant_id,
            subject=str(subject) if subject is not None else None,
            occurred_at=occurred_at or IntelligenceEvent.create(
                event_type=event_type,
                source=principal.service_id,
                trace_id=trace_id,
            ).occurred_at,
            data=data,
        )

        try:
            handled = event_service.publish(event)
        except DuplicateEventError:
            return jsonify({"error": "duplicate event"}), 409
        except Exception:
            return jsonify({"error": "event ingestion failed"}), 502

        return jsonify(
            {
                "event_id": event.event_id,
                "trace_id": event.trace_id,
                "accepted": True,
                "handlers_invoked": handled,
            }
        ), 202

    return blueprint
