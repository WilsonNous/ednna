from __future__ import annotations

import os


def servicebus_outbox_enabled() -> bool:
    return os.getenv("SERVICEBUS_OUTBOX_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
