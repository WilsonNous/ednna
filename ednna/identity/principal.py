from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    service_id: str | None = None
    roles: tuple[str, ...] = field(default_factory=tuple)
    permissions: tuple[str, ...] = field(default_factory=tuple)
