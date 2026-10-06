from __future__ import annotations

import os
from enum import Enum


class ActionExecutionMode(str, Enum):
    DRY_RUN = "dry_run"
    LIVE = "live"


def action_execution_mode() -> ActionExecutionMode:
    value = os.getenv("ACTION_EXECUTION_MODE", "dry_run").strip().lower()
    try:
        return ActionExecutionMode(value)
    except ValueError:
        return ActionExecutionMode.DRY_RUN
