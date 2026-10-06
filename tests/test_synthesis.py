from ednna.orchestration.contracts import IntelligenceResponse
from ednna.orchestration.executor import PlanExecutionResult
from ednna.orchestration.planner import OrchestrationPlan
from ednna.orchestration.synthesis import DeterministicSynthesizer


def test_synthesizer_preserves_specialist_provenance_and_evidence():
    execution = PlanExecutionResult(
        trace_id="trace-1",
        plan=OrchestrationPlan(goal="risk", steps=()),
        responses=(
            IntelligenceResponse(
                specialist_id="eddy",
                capability="edi.status.get",
                status="success",
                output={"pending": 2},
                confidence=0.96,
                evidence=({"type": "edi_operation", "id": "op-1"},),
                trace_id="trace-1",
            ),
            IntelligenceResponse(
                specialist_id="finance",
                capability="finance.exposure.get",
                status="success",
                output={"exposure": 15000},
                confidence=0.88,
                evidence=({"type": "invoice", "id": "inv-1"},),
                trace_id="trace-1",
            ),
        ),
    )

    result = DeterministicSynthesizer().synthesize(execution)

    assert len(result.findings) == 2
    assert result.findings[0].specialist_id == "eddy"
    assert result.findings[1].specialist_id == "finance"
    assert result.minimum_confidence == 0.88
    assert result.findings[0].evidence[0]["id"] == "op-1"


def test_synthesizer_propagates_human_requirement_and_warnings():
    execution = PlanExecutionResult(
        trace_id="trace-2",
        plan=OrchestrationPlan(goal="risk", steps=()),
        responses=(
            IntelligenceResponse(
                specialist_id="eddy",
                capability="edi.issue.inspect",
                status="blocked",
                output={},
                confidence=0.7,
                warnings=("Ambiguous mapping",),
                requires_human=True,
                trace_id="trace-2",
            ),
        ),
    )

    result = DeterministicSynthesizer().synthesize(execution)

    assert result.requires_human is True
    assert result.warnings == ("Ambiguous mapping",)
