from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from ednna.bootstrap import build_multiagent_runtime
from ednna.orchestration.discovery import CapabilityDiscovery
from ednna.orchestration.executor import ExecutionContext, PlanExecutor
from ednna.orchestration.planner import Planner
from ednna.orchestration.service import OrchestrationService
from ednna.orchestration.synthesis import DeterministicSynthesizer

from .feature_flags import orchestrated_chat_enabled


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatResult:
    response: str
    intent: str
    mode: str
    trace_id: str | None = None
    confidence: float | None = None


def try_orchestrated_chat(
    message: str,
    user_id: str | None = None,
    conversation_id: str | None = None,
) -> ChatResult | None:
    """Try the EDNNA 2.0 QUERY path; return None to use the legacy fallback."""
    if not orchestrated_chat_enabled():
        return None

    try:
        registry, gateway, _availability = build_multiagent_runtime()
        planner = Planner(CapabilityDiscovery(registry))
        plan = planner.plan(message)

        if not plan.steps:
            return None

        executor = PlanExecutor(planner, OrchestrationService(gateway))
        execution = executor.execute_plan(
            plan,
            input={"message": message},
            context=ExecutionContext(
                user_id=user_id,
                conversation_id=conversation_id,
            ),
        )
        synthesis = DeterministicSynthesizer().synthesize(execution)

        if not synthesis.findings:
            return None

        lines = []
        for finding in synthesis.findings:
            payload = json.dumps(
                finding.output,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
            lines.append(
                f"**{finding.specialist_id.upper()}** "
                f"({finding.capability}): {payload}"
            )

        if synthesis.warnings:
            lines.append("Avisos: " + "; ".join(synthesis.warnings))
        if synthesis.requires_human:
            lines.append("Esta consulta requer uma decisão humana antes de qualquer ação.")

        return ChatResult(
            response="\n\n".join(lines),
            intent="orchestration",
            mode="orchestrated",
            trace_id=execution.trace_id,
            confidence=synthesis.minimum_confidence,
        )
    except Exception:
        logger.exception("Orchestrated chat failed; using legacy fallback")
        return None
