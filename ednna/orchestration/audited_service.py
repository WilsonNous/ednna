from __future__ import annotations

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
            self._recorder.record_failure("query.failed", traced, exc)
            raise
        self._recorder.record_response("query.completed", traced, response)
        return response

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        traced = ensure_trace(request)
        self._recorder.record_request("action.requested", traced)
        try:
            response = self._service.action(traced)
        except Exception as exc:
            self._recorder.record_failure("action.failed", traced, exc)
            raise
        self._recorder.record_response("action.completed", traced, response)
        return response
