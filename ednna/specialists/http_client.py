from __future__ import annotations

from dataclasses import asdict
from typing import Any

import requests

from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse
from ednna.specialists.action_status import SpecialistActionState, SpecialistActionStatus
from ednna.specialists.handshake import SpecialistHandshake
from ednna.specialists.protocol import (
    CONTRACT_VERSION,
    CONTRACT_VERSION_HEADER,
    validate_contract_version,
)


class SpecialistTransportError(RuntimeError):
    pass


class HttpSpecialistClient:
    """HTTP transport for specialist intelligence contracts."""

    def __init__(
        self,
        specialist_id: str,
        base_url: str,
        api_token: str,
        timeout_seconds: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        self._specialist_id = specialist_id
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    def handshake(self) -> SpecialistHandshake:
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            CONTRACT_VERSION_HEADER: CONTRACT_VERSION,
        }

        try:
            response = self._session.get(
                f"{self._base_url}/api/intelligence/handshake",
                headers=headers,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            body: dict[str, Any] = response.json()

            response_headers = getattr(response, "headers", {}) or {}
            validate_contract_version(response_headers.get(CONTRACT_VERSION_HEADER))
            validate_contract_version(body.get("contract_version"))
        except (requests.RequestException, ValueError) as exc:
            raise SpecialistTransportError(
                f"Specialist '{self._specialist_id}' handshake failed"
            ) from exc

        return SpecialistHandshake(
            specialist_id=str(body.get("specialist_id", "")),
            contract_version=str(body.get("contract_version", "")),
            capabilities=tuple(str(item) for item in body.get("capabilities", [])),
            status=str(body.get("status", "unknown")),
        )

    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        return self._post("/api/intelligence/query", request)

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        return self._post("/api/intelligence/action", request)

    def action_status(
        self,
        idempotency_key: str,
        trace_id: str | None = None,
    ) -> SpecialistActionStatus:
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            CONTRACT_VERSION_HEADER: CONTRACT_VERSION,
            "X-Trace-Id": trace_id or "",
        }

        try:
            response = self._session.get(
                f"{self._base_url}/api/intelligence/actions/{idempotency_key}",
                headers=headers,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            body: dict[str, Any] = response.json()

            response_headers = getattr(response, "headers", {}) or {}
            validate_contract_version(response_headers.get(CONTRACT_VERSION_HEADER))
            validate_contract_version(body.get("contract_version"))
            state = SpecialistActionState(str(body.get("state", "unknown")))
        except (requests.RequestException, ValueError) as exc:
            raise SpecialistTransportError(
                f"Specialist '{self._specialist_id}' action status lookup failed"
            ) from exc

        return SpecialistActionStatus(
            specialist_id=str(body.get("specialist_id", self._specialist_id)),
            idempotency_key=idempotency_key,
            state=state,
            trace_id=body.get("trace_id", trace_id),
            evidence=tuple(body.get("evidence", [])),
            reference=body.get("reference"),
        )

    def _post(
        self,
        path: str,
        request: IntelligenceRequest,
    ) -> IntelligenceResponse:
        payload = asdict(request)
        payload["contract_version"] = CONTRACT_VERSION
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
            "X-Trace-Id": request.trace_id or "",
            CONTRACT_VERSION_HEADER: CONTRACT_VERSION,
        }

        try:
            response = self._session.post(
                f"{self._base_url}{path}",
                json=payload,
                headers=headers,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            body: dict[str, Any] = response.json()

            response_headers = getattr(response, "headers", {}) or {}
            validate_contract_version(response_headers.get(CONTRACT_VERSION_HEADER))
            validate_contract_version(body.get("contract_version"))
        except (requests.RequestException, ValueError) as exc:
            raise SpecialistTransportError(
                f"Specialist '{self._specialist_id}' request failed"
            ) from exc

        return IntelligenceResponse(
            specialist_id=body.get("specialist_id", self._specialist_id),
            capability=body.get("capability", request.capability),
            status=body.get("status", "unknown"),
            output=body.get("output", {}),
            confidence=body.get("confidence"),
            evidence=tuple(body.get("evidence", [])),
            warnings=tuple(body.get("warnings", [])),
            requires_human=bool(body.get("requires_human", False)),
            trace_id=body.get("trace_id", request.trace_id),
        )
