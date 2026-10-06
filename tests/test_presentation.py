from ednna.orchestration.synthesis import SpecialistFinding, SynthesisResult
from ednna.orchestration.presentation import ExecutivePresenter


def test_presenter_builds_executive_response_from_findings_only():
    synthesis = SynthesisResult(
        trace_id="trace-1",
        findings=(
            SpecialistFinding(
                specialist_id="eddy",
                capability="edi.status.get",
                status="success",
                output={"pending": 2},
                confidence=0.95,
                evidence=({"type": "operation", "id": "op-1"},),
                warnings=(),
                requires_human=False,
            ),
            SpecialistFinding(
                specialist_id="finance",
                capability="finance.exposure.get",
                status="success",
                output={"exposure": 15000},
                confidence=0.88,
                evidence=({"type": "invoice", "id": "inv-1"},),
                warnings=("Exposure above threshold",),
                requires_human=True,
            ),
        ),
        minimum_confidence=0.88,
        requires_human=True,
        warnings=("Exposure above threshold",),
    )

    response = ExecutivePresenter().present(synthesis)

    assert response.trace_id == "trace-1"
    assert "eddy" in response.summary
    assert "finance" in response.summary
    assert response.requires_human is True
    assert response.minimum_confidence == 0.88
    assert any(section.title == "Warnings" for section in response.sections)
    assert any(section.title == "Human decision required" for section in response.sections)


def test_presenter_handles_empty_synthesis():
    synthesis = SynthesisResult(
        trace_id="trace-empty",
        findings=(),
        minimum_confidence=None,
        requires_human=False,
        warnings=(),
    )

    response = ExecutivePresenter().present(synthesis)

    assert response.summary == "No specialist findings were produced."
    assert response.sections == ()
