from __future__ import annotations

from dataclasses import replace

from ednna.governance.action_control import ActionAuthorization, ActionAuthorizer
from ednna.governance.idempotency import IdempotencyStore
from ednna.observability.tracing import ensure_trace

from .contracts import IntelligenceRequest, IntelligenceResponse
from .service import OrchestrationService


class ControlledActionService:
    """Execute ACTION only after policy, approval and idempotency checks."""

    def __init__(
        self,
        orchestration: OrchestrationService,
        authorizer: ActionAuthorizer,
        idempotency: IdempotencyStore,
    ) -> None:
        self._orchestration = orchestration
        self._authorizer = authorizer
        self._idempotency = idempotency

    def execute(
        self,
        request: IntelligenceRequest,
        authorization: ActionAuthorization,
    ) -> IntelligenceResponse:
        traced = ensure_trace(request)
        if traced.capability != authorization.capability:
            authorization = replace(
                authorization,
                capability=traced.capability,
            )

        self._authorizer.authorize(authorization)
        self._idempotency.reserve(authorization.idempotency_key)
        return self._orchestration.action(traced)
