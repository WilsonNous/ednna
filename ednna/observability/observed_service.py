from __future__ import annotations

from time import perf_counter

from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse
from ednna.orchestration.service import OrchestrationService

from .metrics import MetricsRecorder


class ObservedOrchestrationService:
    """Record specialist-call outcomes and latency around orchestration."""

    def __init__(
        self,
        service: OrchestrationService,
        metrics: MetricsRecorder,
    ) -> None:
        self._service = service
        self._metrics = metrics

    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        return self._execute("query", request, self._service.query)

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        return self._execute("action", request, self._service.action)

    def _execute(self, operation: str, request: IntelligenceRequest, callback):
        tags = {
            "operation": operation,
            "capability": request.capability,
        }
        started = perf_counter()
        self._metrics.increment("ednna.orchestration.request", tags=tags)

        try:
            response = callback(request)
        except Exception as exc:
            error_tags = {
                **tags,
                "error_type": type(exc).__name__,
            }
            self._metrics.increment("ednna.orchestration.error", tags=error_tags)
            raise
        finally:
            self._metrics.observe(
                "ednna.orchestration.latency_ms",
                (perf_counter() - started) * 1000.0,
                tags=tags,
            )

        result_tags = {
            **tags,
            "specialist": response.specialist_id,
            "status": response.status,
        }
        self._metrics.increment("ednna.orchestration.response", tags=result_tags)

        if response.requires_human:
            self._metrics.increment(
                "ednna.orchestration.requires_human",
                tags={
                    "specialist": response.specialist_id,
                    "capability": response.capability,
                },
            )

        return response
