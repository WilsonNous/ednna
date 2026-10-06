from __future__ import annotations

import os


def specialist_health_worker_enabled() -> bool:
    return os.getenv("SPECIALIST_HEALTH_WORKER_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
