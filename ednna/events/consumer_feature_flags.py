from __future__ import annotations

import os


def servicebus_consumer_enabled() -> bool:
    return os.getenv("SERVICEBUS_CONSUMER_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
