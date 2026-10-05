from __future__ import annotations

from ednna.audit.recorder import AuditRecorder

from .contracts import IntelligenceRequest, IntelligenceResponse
from .service import OrchestrationService


class AuditedOrchestrationService:
    """Decorator that records orchestration activity without coupling audit storage."""

    def __init__(self, service: OrchestrationService, recorder: AuditRecorder) -> None:
        self._service = service
        self._recorder = recorder

    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        self._recorder.record_request("query.requested", request)
        response = self._service.query(request)
        self._recorder.record_response("query.completed", request, response)
        return response

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        self._recorder.record_request("action.requested", request)
        response = self._service.action(request)
        self._recorder.record_response("action.completed", request, response)
        return response
