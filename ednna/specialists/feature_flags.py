from __future__ import annotations

import os


def eddy_enabled() -> bool:
    return os.getenv("EDDY_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
