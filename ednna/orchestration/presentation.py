from __future__ import annotations

from dataclasses import dataclass

from .synthesis import SynthesisResult


@dataclass(frozen=True)
class ExecutiveSection:
    title: str
    items: tuple[str, ...]


@dataclass(frozen=True)
class ExecutiveResponse:
    trace_id: str
    summary: str
    sections: tuple[ExecutiveSection, ...]
    requires_human: bool
    minimum_confidence: float | None


class ExecutivePresenter:
    """Create a concise executive response strictly from structured findings."""

    def present(self, synthesis: SynthesisResult) -> ExecutiveResponse:
        summary = self._build_summary(synthesis)
        findings = tuple(
            self._finding_line(finding)
            for finding in synthesis.findings
        )

        warnings = tuple(synthesis.warnings)
        human_items = tuple(
            self._finding_line(finding)
            for finding in synthesis.findings
            if finding.requires_human
        )

        sections: list[ExecutiveSection] = []
        if findings:
            sections.append(ExecutiveSection("Findings", findings))
        if warnings:
            sections.append(ExecutiveSection("Warnings", warnings))
        if human_items:
            sections.append(ExecutiveSection("Human decision required", human_items))

        return ExecutiveResponse(
            trace_id=synthesis.trace_id,
            summary=summary,
            sections=tuple(sections),
            requires_human=synthesis.requires_human,
            minimum_confidence=synthesis.minimum_confidence,
        )

    @staticmethod
    def _build_summary(synthesis: SynthesisResult) -> str:
        count = len(synthesis.findings)
        if count == 0:
            return "No specialist findings were produced."

        specialists = sorted({finding.specialist_id for finding in synthesis.findings})
        summary = (
            f"{count} finding(s) from {len(specialists)} specialist(s): "
            f"{', '.join(specialists)}."
        )

        if synthesis.requires_human:
            summary += " Human decision is required."

        if synthesis.minimum_confidence is not None:
            summary += f" Minimum confidence: {synthesis.minimum_confidence:.2f}."

        return summary

    @staticmethod
    def _finding_line(finding) -> str:
        evidence_count = len(finding.evidence)
        confidence = (
            f"{finding.confidence:.2f}"
            if finding.confidence is not None
            else "n/a"
        )
        return (
            f"[{finding.specialist_id}] {finding.capability}: "
            f"status={finding.status}; confidence={confidence}; "
            f"evidence={evidence_count}"
        )
