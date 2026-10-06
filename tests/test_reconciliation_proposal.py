from ednna.governance.reconciliation_proposal import (
    ReconciliationProposalKind,
    ReconciliationProposalService,
)
from ednna.specialists.action_status import SpecialistActionState, SpecialistActionStatus


def make_status(state: SpecialistActionState):
    return SpecialistActionStatus(
        specialist_id="eddy",
        idempotency_key="action-key-1",
        state=state,
        trace_id="trace-1",
        evidence=({"type": "receipt", "id": "r-1"},),
        reference="eddy:r-1",
    )


def test_succeeded_status_proposes_confirmation_without_automatic_mutation():
    proposal = ReconciliationProposalService().propose(
        make_status(SpecialistActionState.SUCCEEDED)
    )

    assert proposal.kind is ReconciliationProposalKind.CONFIRM_SUCCEEDED
    assert proposal.automatic is False
    assert proposal.reason_code == "specialist_reports_succeeded"
    assert proposal.evidence_count == 1


def test_not_executed_status_proposes_safe_manual_confirmation():
    proposal = ReconciliationProposalService().propose(
        make_status(SpecialistActionState.NOT_EXECUTED)
    )

    assert proposal.kind is ReconciliationProposalKind.CONFIRM_NOT_EXECUTED
    assert proposal.automatic is False


def test_in_progress_status_proposes_wait():
    proposal = ReconciliationProposalService().propose(
        make_status(SpecialistActionState.IN_PROGRESS)
    )

    assert proposal.kind is ReconciliationProposalKind.WAIT
    assert proposal.automatic is False


def test_unknown_status_proposes_investigation():
    proposal = ReconciliationProposalService().propose(
        make_status(SpecialistActionState.UNKNOWN)
    )

    assert proposal.kind is ReconciliationProposalKind.INVESTIGATE
    assert proposal.automatic is False
