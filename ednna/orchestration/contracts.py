from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OperationKind(str, Enum):
    QUERY = "query"
    ACTION = "action"


@dataclass(frozen=True)
class Capability:
    name: str
    kind: OperationKind
    description: str = ""


@dataclass(frozen=True)
class SpecialistDescriptor:
    specialist_id: str
    name: str
    domain: str
    description: str
    capabilities: tuple[Capability, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class IntelligenceRequest:
    capability: str
    input: dict[str, Any]
    user_id: str | None = None
    tenant_id: str | None = None
    conversation_id: str | None = None
    trace_id: str | None = None


@dataclass(frozen=True)
class IntelligenceResponse:
    specialist_id: str
    capability: str
    status: str
    output: dict[str, Any]
    confidence: float | None = None
    evidence: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    requires_human: bool = False
    trace_id: str | None = None
