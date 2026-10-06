from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from ednna.orchestration.contracts import IntelligenceResponse

from .approvals import (
    ApprovalRequest,
    ApprovalStatus,
    ApprovalStore,
    new_approval_request,
)


class ApprovalNotFoundError(LookupError):
    pass


class HumanDecisionService:
    def __init__(self, store: ApprovalStore) -> None:
        self._store = store

    def create_from_response(
        self,
        response: IntelligenceResponse,
        reason: str | None = None,
        tenant_id: str | None = None,
        requested_by: str | None = None,
    ) -> ApprovalRequest | None:
        if not response.requires_human:
            return None
        if not response.trace_id:
            raise ValueError("trace_id is required for human approval")

        approval = new_approval_request(
            trace_id=response.trace_id,
            capability=response.capability,
            specialist_id=response.specialist_id,
            reason=reason or self._default_reason(response),
            tenant_id=tenant_id,
            requested_by=requested_by,
        )
        self._store.save(approval)
        return approval

    def decide(
        self,
        approval_id: str,
        approved: bool,
        decided_by: str,
        note: str | None = None,
    ) -> ApprovalRequest:
        current = self._store.get(approval_id)
        if current is None:
            raise ApprovalNotFoundError(approval_id)

        decided = replace(
            current,
            status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
            decided_at=datetime.now(timezone.utc),
            decided_by=decided_by,
            decision_note=note,
        )
        self._store.save(decided)
        return decided

    @staticmethod
    def _default_reason(response: IntelligenceResponse) -> str:
        if response.warnings:
            return response.warnings[0]
        return "Specialist requested human decision"
