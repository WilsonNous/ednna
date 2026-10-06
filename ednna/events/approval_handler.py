from __future__ import annotations

from ednna.governance.approvals import ApprovalStore, new_approval_request

from .contracts import IntelligenceEvent


class ApprovalEventHandler:
    """Translate explicitly mapped specialist events into human approval requests."""

    def __init__(self, approvals: ApprovalStore) -> None:
        self._approvals = approvals
        self._capability_by_event_type = {
            "edi.operation.approval_required": "edi.operation.execute",
        }

    def __call__(self, event: IntelligenceEvent) -> None:
        capability = self._capability_by_event_type.get(event.event_type)
        if capability is None:
            return

        reason = str(event.data.get("reason", "")).strip()
        if not reason:
            reason = "Specialist requested human approval"

        approval = new_approval_request(
            trace_id=event.trace_id,
            capability=capability,
            specialist_id=event.source,
            reason=reason,
            tenant_id=event.tenant_id,
            requested_by=event.source,
        )
        self._approvals.save(approval)
