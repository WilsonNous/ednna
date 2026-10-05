from __future__ import annotations

from ednna.audit.events import AuditEvent
from ednna.audit.recorder import AuditRecorder
from ednna.observability.tracing import ensure_trace

from .contracts import IntelligenceRequest, IntelligenceResponse
from .service import OrchestrationService


class AuditedOrchestrationService:
    """Decorator that records orchestration activity without coupling audit storage."""

    def __init__(self, service: OrchestrationService, recorder: AuditRecorder) -> None:
        self._service = service
        self._recorder = recorder

    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        traced = ensure_trace(request)
        self._recorder.record_request("query.requested", traced)
        try:
            response = self._service.query(traced)
        except Exception as exc:
            self._record_failure("query.failed", traced, exc)
            raise
        self._recorder.record_response("query.completed", traced, response)
        return response

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        traced = ensure_trace(request)
        self._recorder.record_request("action.requested", traced)
        try:
            response = self._service.action(traced)
        except Exception as exc:
            self._record_failure("action.failed", traced, exc)
            raise
        self._recorder.record_response("action.completed", traced, response)
        return response

    def _record_failure(
        self,
        event_type: str,
        request: IntelligenceRequest,
        exc: Exception,
    ) -> None:
        self._recorder._store.append(
            AuditEvent(
                event_type=event_type,
                trace_id=request.trace_id or "",
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                conversation_id=request.conversation_id,
                capability=request.capability,
                status="failed",
                details={"error_type": type(exc).__name__},
            )
        )
