from __future__ import annotations

from dataclasses import dataclass

from .principal import Principal


@dataclass(frozen=True)
class RequestIdentity:
    principal: Principal
    correlation_id: str | None = None
