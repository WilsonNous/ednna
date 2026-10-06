from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol


class ActionExecutionStatus(str, Enum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    UNCERTAIN = "uncertain"
    RECONCILED_SUCCEEDED = "reconciled_succeeded"
    RECONCILED_NOT_EXECUTED = "reconciled_not_executed"


class DuplicateActionExecutionError(RuntimeError):
    pass


class ActionExecutionNotFoundError(LookupError):
    pass


class ActionExecutionNotReconcilableError(ValueError):
    pass


@dataclass(frozen=True)
class ActionExecutionRecord:
    idempotency_key: str
    trace_id: str
    capability: str
    tenant_id: str | None = None
    requested_by: str | None = None
    status: ActionExecutionStatus = ActionExecutionStatus.STARTED
    started_at: datetime = datetime.min.replace(tzinfo=timezone.utc)
    completed_at: datetime | None = None
    specialist_id: str | None = None
    response_status: str | None = None
    evidence_count: int = 0
    error_type: str | None = None
    reconciled_at: datetime | None = None
    reconciled_by: str | None = None
    reconciliation_note: str | None = None
    reconciliation_reference: str | None = None


class ActionExecutionLedger(Protocol):
    def get(self, idempotency_key: str) -> ActionExecutionRecord | None:
        ...

    def start(
        self,
        idempotency_key: str,
        trace_id: str,
        capability: str,
        tenant_id: str | None = None,
        requested_by: str | None = None,
    ) -> ActionExecutionRecord:
        ...

    def succeed(
        self,
        idempotency_key: str,
        specialist_id: str,
        response_status: str,
        evidence_count: int,
    ) -> ActionExecutionRecord:
        ...

    def uncertain(
        self,
        idempotency_key: str,
        error_type: str,
    ) -> ActionExecutionRecord:
        ...

    def reconcile(
        self,
        idempotency_key: str,
        status: ActionExecutionStatus,
        reconciled_by: str,
        note: str,
        reference: str,
    ) -> ActionExecutionRecord:
        ...


class InMemoryActionExecutionLedger:
    def __init__(self) -> None:
        self._records: dict[str, ActionExecutionRecord] = {}

    def start(
        self,
        idempotency_key: str,
        trace_id: str,
        capability: str,
        tenant_id: str | None = None,
        requested_by: str | None = None,
    ) -> ActionExecutionRecord:
        if idempotency_key in self._records:
            raise DuplicateActionExecutionError(idempotency_key)

        record = ActionExecutionRecord(
            idempotency_key=idempotency_key,
            trace_id=trace_id,
            capability=capability,
            tenant_id=tenant_id,
            requested_by=requested_by,
            started_at=datetime.now(timezone.utc),
        )
        self._records[idempotency_key] = record
        return record

    def get(self, idempotency_key: str) -> ActionExecutionRecord | None:
        return self._records.get(idempotency_key)

    def succeed(
        self,
        idempotency_key: str,
        specialist_id: str,
        response_status: str,
        evidence_count: int,
    ) -> ActionExecutionRecord:
        current = self._require(idempotency_key)
        updated = replace(
            current,
            status=ActionExecutionStatus.SUCCEEDED,
            completed_at=datetime.now(timezone.utc),
            specialist_id=specialist_id,
            response_status=response_status,
            evidence_count=evidence_count,
            error_type=None,
        )
        self._records[idempotency_key] = updated
        return updated

    def uncertain(
        self,
        idempotency_key: str,
        error_type: str,
    ) -> ActionExecutionRecord:
        current = self._require(idempotency_key)
        updated = replace(
            current,
            status=ActionExecutionStatus.UNCERTAIN,
            completed_at=datetime.now(timezone.utc),
            error_type=error_type,
        )
        self._records[idempotency_key] = updated
        return updated

    def reconcile(
        self,
        idempotency_key: str,
        status: ActionExecutionStatus,
        reconciled_by: str,
        note: str,
        reference: str,
    ) -> ActionExecutionRecord:
        current = self._require(idempotency_key)
        allowed = {
            ActionExecutionStatus.RECONCILED_SUCCEEDED,
            ActionExecutionStatus.RECONCILED_NOT_EXECUTED,
        }
        if current.status is not ActionExecutionStatus.UNCERTAIN or status not in allowed:
            raise ActionExecutionNotReconcilableError(idempotency_key)

        updated = replace(
            current,
            status=status,
            reconciled_at=datetime.now(timezone.utc),
            reconciled_by=reconciled_by,
            reconciliation_note=note,
            reconciliation_reference=reference,
        )
        self._records[idempotency_key] = updated
        return updated

    def _require(self, idempotency_key: str) -> ActionExecutionRecord:
        current = self._records.get(idempotency_key)
        if current is None:
            raise ActionExecutionNotFoundError(idempotency_key)
        return current
