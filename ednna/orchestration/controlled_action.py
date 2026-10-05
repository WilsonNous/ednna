from __future__ import annotations

from ednna.governance.action_control import ActionAuthorization, ActionAuthorizer
from ednna.governance.idempotency import IdempotencyStore
from ednna.observability.tracing import ensure_trace

from .contracts import IntelligenceRequest, IntelligenceResponse, OperationKind
from .gateway import IntelligenceGateway


class ActionCapabilityMismatchError(ValueError):
    pass


class ControlledActionService:
    """Execute ACTION only after policy, approval and idempotency checks."""

    def __init__(
        self,
        gateway: IntelligenceGateway,
        authorizer: ActionAuthorizer,
        idempotency: IdempotencyStore,
    ) -> None:
        self._gateway = gateway
        self._authorizer = authorizer
        self._idempotency = idempotency

    def execute(
        self,
        request: IntelligenceRequest,
        authorization: ActionAuthorization,
    ) -> IntelligenceResponse:
        traced = ensure_trace(request)

        if traced.capability != authorization.capability:
            raise ActionCapabilityMismatchError(
                "Authorization capability does not match requested action"
            )

        self._authorizer.authorize(authorization)
        self._idempotency.reserve(authorization.idempotency_key)
        return self._gateway.dispatch(traced, OperationKind.ACTION)
