from __future__ import annotations

import os
from enum import Enum


class ActionExecutionMode(str, Enum):
    DRY_RUN = "dry_run"
    LIVE = "live"


def action_execution_mode_value() -> str:
    return os.getenv("ACTION_EXECUTION_MODE", "dry_run").strip().lower()


def action_execution_mode_valid() -> bool:
    return action_execution_mode_value() in {
        ActionExecutionMode.DRY_RUN.value,
        ActionExecutionMode.LIVE.value,
    }


def action_execution_mode() -> ActionExecutionMode:
    value = action_execution_mode_value()
    try:
        return ActionExecutionMode(value)
    except ValueError:
        return ActionExecutionMode.DRY_RUN
