from __future__ import annotations

from .events import AuditEvent
from .store import AuditStore
from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse


class AuditRecorder:
    def __init__(self, store: AuditStore) -> None:
        self._store = store

    def record_request(
        self,
        event_type: str,
        request: IntelligenceRequest,
        specialist_id: str | None = None,
    ) -> None:
        if request.trace_id is None:
            return

        self._store.append(
            AuditEvent(
                event_type=event_type,
                trace_id=request.trace_id,
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                conversation_id=request.conversation_id,
                specialist_id=specialist_id,
                capability=request.capability,
                details={"input_keys": sorted(request.input.keys())},
            )
        )

    def record_response(
        self,
        event_type: str,
        request: IntelligenceRequest,
        response: IntelligenceResponse,
    ) -> None:
        if request.trace_id is None:
            return

        self._store.append(
            AuditEvent(
                event_type=event_type,
                trace_id=request.trace_id,
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                conversation_id=request.conversation_id,
                specialist_id=response.specialist_id,
                capability=response.capability,
                status=response.status,
                confidence=response.confidence,
                requires_human=response.requires_human,
                details={
                    "evidence_count": len(response.evidence),
                    "warning_count": len(response.warnings),
                },
            )
        )
