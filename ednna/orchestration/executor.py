from __future__ import annotations

from dataclasses import dataclass

from ednna.observability.tracing import new_trace_id

from .contracts import IntelligenceRequest, IntelligenceResponse, OperationKind
from .planner import OrchestrationPlan, Planner
from .service import OrchestrationService


@dataclass(frozen=True)
class ExecutionContext:
    user_id: str | None = None
    tenant_id: str | None = None
    conversation_id: str | None = None


@dataclass(frozen=True)
class PlanExecutionResult:
    trace_id: str
    plan: OrchestrationPlan
    responses: tuple[IntelligenceResponse, ...]


class PlanExecutor:
    """Execute planner steps through the governed orchestration boundary."""

    def __init__(self, planner: Planner, service: OrchestrationService) -> None:
        self._planner = planner
        self._service = service

    def execute(
        self,
        goal: str,
        input: dict,
        context: ExecutionContext | None = None,
    ) -> PlanExecutionResult:
        return self.execute_plan(
            self._planner.plan(goal),
            input=input,
            context=context,
        )

    def execute_plan(
        self,
        plan: OrchestrationPlan,
        input: dict,
        context: ExecutionContext | None = None,
    ) -> PlanExecutionResult:
        active_context = context or ExecutionContext()
        trace_id = new_trace_id()
        responses: list[IntelligenceResponse] = []

        for step in plan.steps:
            request = IntelligenceRequest(
                capability=step.capability,
                input=input,
                user_id=active_context.user_id,
                tenant_id=active_context.tenant_id,
                conversation_id=active_context.conversation_id,
                trace_id=trace_id,
            )

            if step.operation is OperationKind.QUERY:
                response = self._service.query(request)
            else:
                response = self._service.action(request)

            responses.append(response)

        return PlanExecutionResult(
            trace_id=trace_id,
            plan=plan,
            responses=tuple(responses),
        )
