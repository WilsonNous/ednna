from __future__ import annotations

from dataclasses import asdict
from typing import Any

import requests

from ednna.orchestration.contracts import IntelligenceRequest, IntelligenceResponse


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

    def query(self, request: IntelligenceRequest) -> IntelligenceResponse:
        return self._post("/api/intelligence/query", request)

    def action(self, request: IntelligenceRequest) -> IntelligenceResponse:
        return self._post("/api/intelligence/action", request)

    def _post(
        self,
        path: str,
        request: IntelligenceRequest,
    ) -> IntelligenceResponse:
        payload = asdict(request)
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
            "X-Trace-Id": request.trace_id or "",
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
