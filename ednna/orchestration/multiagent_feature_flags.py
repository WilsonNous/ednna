from __future__ import annotations

import os


def multiagent_query_api_enabled() -> bool:
    return os.getenv("MULTIAGENT_QUERY_API_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
