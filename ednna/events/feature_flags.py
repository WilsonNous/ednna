from __future__ import annotations

import os


def event_ingress_api_enabled() -> bool:
    return os.getenv("EVENT_INGRESS_API_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
