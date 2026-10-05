from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol
from uuid import uuid4


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    trace_id: str
    capability: str
    specialist_id: str
    reason: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: datetime | None = None
    decided_by: str | None = None
    decision_note: str | None = None


class ApprovalStore(Protocol):
    def save(self, approval: ApprovalRequest) -> None:
        ...

    def get(self, approval_id: str) -> ApprovalRequest | None:
        ...


class InMemoryApprovalStore:
    def __init__(self) -> None:
        self._items: dict[str, ApprovalRequest] = {}

    def save(self, approval: ApprovalRequest) -> None:
        self._items[approval.approval_id] = approval

    def get(self, approval_id: str) -> ApprovalRequest | None:
        return self._items.get(approval_id)


def new_approval_request(
    trace_id: str,
    capability: str,
    specialist_id: str,
    reason: str,
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_id=str(uuid4()),
        trace_id=trace_id,
        capability=capability,
        specialist_id=specialist_id,
        reason=reason,
    )
