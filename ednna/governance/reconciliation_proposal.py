from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ednna.specialists.action_status import SpecialistActionState, SpecialistActionStatus


class ReconciliationProposalKind(str, Enum):
    CONFIRM_SUCCEEDED = "confirm_succeeded"
    CONFIRM_NOT_EXECUTED = "confirm_not_executed"
    WAIT = "wait"
    INVESTIGATE = "investigate"


@dataclass(frozen=True)
class ReconciliationProposal:
    kind: ReconciliationProposalKind
    automatic: bool
    reason_code: str
    specialist_id: str
    idempotency_key: str
    evidence_count: int
    reference: str | None = None


class ReconciliationProposalService:
    """Map remote action status to a non-binding reconciliation proposal."""

    def propose(self, status: SpecialistActionStatus) -> ReconciliationProposal:
        mapping = {
            SpecialistActionState.SUCCEEDED: (
                ReconciliationProposalKind.CONFIRM_SUCCEEDED,
                "specialist_reports_succeeded",
            ),
            SpecialistActionState.NOT_EXECUTED: (
                ReconciliationProposalKind.CONFIRM_NOT_EXECUTED,
                "specialist_reports_not_executed",
            ),
            SpecialistActionState.IN_PROGRESS: (
                ReconciliationProposalKind.WAIT,
                "specialist_reports_in_progress",
            ),
            SpecialistActionState.UNKNOWN: (
                ReconciliationProposalKind.INVESTIGATE,
                "specialist_status_unknown",
            ),
        }
        kind, reason_code = mapping[status.state]
        return ReconciliationProposal(
            kind=kind,
            automatic=False,
            reason_code=reason_code,
            specialist_id=status.specialist_id,
            idempotency_key=status.idempotency_key,
            evidence_count=len(status.evidence),
            reference=status.reference,
        )
