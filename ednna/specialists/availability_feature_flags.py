from __future__ import annotations

import os


def specialist_availability_durable() -> bool:
    return os.getenv("SPECIALIST_AVAILABILITY_DURABLE", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
