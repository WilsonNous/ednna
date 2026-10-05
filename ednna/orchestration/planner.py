from __future__ import annotations

from dataclasses import dataclass

from .contracts import OperationKind
from .discovery import CapabilityDiscovery


@dataclass(frozen=True)
class PlanStep:
    specialist_id: str
    capability: str
    operation: OperationKind
    score: float


@dataclass(frozen=True)
class OrchestrationPlan:
    goal: str
    steps: tuple[PlanStep, ...]


class Planner:
    """Create an explicit, auditable plan from discovered capabilities."""

    def __init__(
        self,
        discovery: CapabilityDiscovery,
        minimum_score: float = 2.0,
        maximum_steps: int = 3,
    ) -> None:
        self._discovery = discovery
        self._minimum_score = minimum_score
        self._maximum_steps = maximum_steps

    def plan(
        self,
        goal: str,
        include_actions: bool = False,
    ) -> OrchestrationPlan:
        matches = self._discovery.search(goal, limit=self._maximum_steps * 2)
        steps = tuple(
            PlanStep(
                specialist_id=match.specialist_id,
                capability=match.capability.name,
                operation=match.capability.kind,
                score=match.score,
            )
            for match in matches
            if match.score >= self._minimum_score
            and (include_actions or match.capability.kind is OperationKind.QUERY)
        )[: self._maximum_steps]
        return OrchestrationPlan(goal=goal, steps=steps)
