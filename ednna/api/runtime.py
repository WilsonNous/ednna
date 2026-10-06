from __future__ import annotations

import os

from flask import Blueprint, jsonify

from ednna.chat.feature_flags import orchestrated_chat_enabled
from ednna.events.feature_flags import event_ingress_api_enabled
from ednna.governance.action_feature_flags import action_api_enabled
from ednna.governance.feature_flags import approval_api_enabled
from ednna.orchestration.multiagent_feature_flags import multiagent_query_api_enabled
from ednna.specialists.feature_flags import eddy_enabled


def _flag(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def create_runtime_blueprint() -> Blueprint:
    blueprint = Blueprint("runtime_api", __name__, url_prefix="/api")

    @blueprint.get("/runtime")
    def runtime():
        return jsonify(
            {
                "platform": "EDNNA 2.0",
                "chat_mode": "orchestrated" if orchestrated_chat_enabled() else "legacy",
                "features": {
                    "eddy": eddy_enabled(),
                    "multiagent_query": multiagent_query_api_enabled(),
                    "approval_api": approval_api_enabled(),
                    "action_api": action_api_enabled(),
                    "event_ingress": event_ingress_api_enabled(),
                    "servicebus_outbox": _flag("SERVICEBUS_OUTBOX_ENABLED"),
                    "servicebus_consumer": _flag("SERVICEBUS_CONSUMER_ENABLED"),
                },
                "action_execution_mode": os.getenv(
                    "ACTION_EXECUTION_MODE",
                    "dry_run",
                ),
            }
        )

    return blueprint
