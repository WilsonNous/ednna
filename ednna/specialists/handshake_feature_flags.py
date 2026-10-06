from __future__ import annotations

import os


def specialist_handshake_enforced() -> bool:
    return os.getenv("SPECIALIST_HANDSHAKE_ENFORCED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
