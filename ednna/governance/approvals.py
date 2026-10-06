from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol
from uuid import uuid4


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalAlreadyBoundError(PermissionError):
    pass


class ApprovalNotFoundForBindingError(LookupError):
    pass


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    trace_id: str
    capability: str
    specialist_id: str
    reason: str
    tenant_id: str | None = None
    requested_by: str | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: datetime | None = None
    decided_by: str | None = None
    decision_note: str | None = None
    action_idempotency_key: str | None = None
    action_bound_at: datetime | None = None


class ApprovalStore(Protocol):
    def save(self, approval: ApprovalRequest) -> None:
        ...

    def get(self, approval_id: str) -> ApprovalRequest | None:
        ...

    def bind_action(
        self,
        approval_id: str,
        idempotency_key: str,
    ) -> ApprovalRequest:
        ...


class InMemoryApprovalStore:
    def __init__(self) -> None:
        self._items: dict[str, ApprovalRequest] = {}

    def save(self, approval: ApprovalRequest) -> None:
        self._items[approval.approval_id] = approval

    def get(self, approval_id: str) -> ApprovalRequest | None:
        return self._items.get(approval_id)

    def bind_action(
        self,
        approval_id: str,
        idempotency_key: str,
    ) -> ApprovalRequest:
        current = self._items.get(approval_id)
        if current is None:
            raise ApprovalNotFoundForBindingError(approval_id)

        if current.action_idempotency_key is not None:
            if current.action_idempotency_key == idempotency_key:
                return current
            raise ApprovalAlreadyBoundError(
                "Approval is already bound to another action"
            )

        bound = replace(
            current,
            action_idempotency_key=idempotency_key,
            action_bound_at=datetime.now(timezone.utc),
        )
        self._items[approval_id] = bound
        return bound


def new_approval_request(
    trace_id: str,
    capability: str,
    specialist_id: str,
    reason: str,
    tenant_id: str | None = None,
    requested_by: str | None = None,
) -> ApprovalRequest:
    return ApprovalRequest(
        approval_id=str(uuid4()),
        trace_id=trace_id,
        capability=capability,
        specialist_id=specialist_id,
        reason=reason,
        tenant_id=tenant_id,
        requested_by=requested_by,
    )
