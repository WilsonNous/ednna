from __future__ import annotations

from dataclasses import dataclass

from .contracts import IntelligenceResponse
from .executor import PlanExecutionResult


@dataclass(frozen=True)
class SpecialistFinding:
    specialist_id: str
    capability: str
    status: str
    output: dict
    confidence: float | None
    evidence: tuple[dict, ...]
    warnings: tuple[str, ...]
    requires_human: bool


@dataclass(frozen=True)
class SynthesisResult:
    trace_id: str
    findings: tuple[SpecialistFinding, ...]
    minimum_confidence: float | None
    requires_human: bool
    warnings: tuple[str, ...]


class DeterministicSynthesizer:
    """Combine specialist responses without inventing unsupported conclusions."""

    def synthesize(self, execution: PlanExecutionResult) -> SynthesisResult:
        findings = tuple(self._finding(response) for response in execution.responses)

        confidences = [
            finding.confidence
            for finding in findings
            if finding.confidence is not None
        ]
        warnings = tuple(
            warning
            for finding in findings
            for warning in finding.warnings
        )

        return SynthesisResult(
            trace_id=execution.trace_id,
            findings=findings,
            minimum_confidence=min(confidences) if confidences else None,
            requires_human=any(finding.requires_human for finding in findings),
            warnings=warnings,
        )

    @staticmethod
    def _finding(response: IntelligenceResponse) -> SpecialistFinding:
        return SpecialistFinding(
            specialist_id=response.specialist_id,
            capability=response.capability,
            status=response.status,
            output=response.output,
            confidence=response.confidence,
            evidence=response.evidence,
            warnings=response.warnings,
            requires_human=response.requires_human,
        )
