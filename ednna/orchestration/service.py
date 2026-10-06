from __future__ import annotations

from ednna.governance.policies import GovernancePolicyRegistry
from ednna.observability.tracing import ensure_trace

from .contracts import IntelligenceRequest, IntelligenceResponse, OperationKind
from .gateway import IntelligenceGateway


class OrchestrationService:
    """Application service coordinating tracing, governance and specialist dispatch."""

    def __init__(
        self,
        gateway: IntelligenceGateway,
        policies: GovernancePolicyRegistry | None = None,
    ) -> None:
        self._gateway = gateway
        self._policies = policies or GovernancePolicyRegistry()

    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        traced_request = ensure_trace(request)
        return self._gateway.dispatch(traced_request, OperationKind.QUERY)

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        traced_request = ensure_trace(request)
        self._policies.assert_action_allowed(traced_request.capability)
        return self._gateway.dispatch(traced_request, OperationKind.ACTION)
