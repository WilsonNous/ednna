from __future__ import annotations

import os


def action_api_enabled() -> bool:
    return os.getenv("ACTION_API_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
