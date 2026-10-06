from __future__ import annotations

import os


def approval_api_enabled() -> bool:
    return os.getenv("APPROVAL_API_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
