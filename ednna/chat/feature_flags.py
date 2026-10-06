from __future__ import annotations

import os


def orchestrated_chat_enabled() -> bool:
    return os.getenv("ORCHESTRATED_CHAT_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
