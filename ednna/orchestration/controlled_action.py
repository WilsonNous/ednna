from __future__ import annotations

import logging

from ednna.governance.action_control import ActionAuthorization, ActionAuthorizer
from ednna.governance.action_ledger import ActionExecutionLedger
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
        ledger: ActionExecutionLedger | None = None,
    ) -> None:
        self._gateway = gateway
        self._authorizer = authorizer
        self._idempotency = idempotency
        self._ledger = ledger
        self._logger = logging.getLogger("ednna.action_execution")

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
        self._authorizer.bind(authorization)
        self._idempotency.reserve(authorization.idempotency_key)

        if self._ledger is not None:
            self._ledger.start(
                idempotency_key=authorization.idempotency_key,
                trace_id=traced.trace_id or "",
                capability=traced.capability,
                tenant_id=traced.tenant_id,
                requested_by=traced.user_id,
            )

        try:
            response = self._gateway.dispatch(traced, OperationKind.ACTION)
        except Exception as exc:
            if self._ledger is not None:
                try:
                    self._ledger.uncertain(
                        authorization.idempotency_key,
                        type(exc).__name__,
                    )
                except Exception as ledger_exc:
                    self._logger.error(
                        "action ledger uncertain update failed: %s",
                        type(ledger_exc).__name__,
                    )
            raise

        if self._ledger is not None:
            try:
                self._ledger.succeed(
                    authorization.idempotency_key,
                    specialist_id=response.specialist_id,
                    response_status=response.status,
                    evidence_count=len(response.evidence),
                )
            except Exception as ledger_exc:
                self._logger.error(
                    "action ledger success update failed: %s",
                    type(ledger_exc).__name__,
                )

        return response
