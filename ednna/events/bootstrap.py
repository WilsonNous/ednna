from __future__ import annotations

from ednna.governance.approvals import ApprovalStore

from .approval_handler import ApprovalEventHandler
from .router import EventRouter


def build_event_router(approvals: ApprovalStore) -> EventRouter:
    router = EventRouter()
    router.subscribe(
        "edi.operation.approval_required",
        ApprovalEventHandler(approvals),
    )
    return router
