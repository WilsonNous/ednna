from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from ednna.orchestration.contracts import IntelligenceRequest


def new_trace_id() -> str:
    return str(uuid4())


def ensure_trace(request: IntelligenceRequest) -> IntelligenceRequest:
    if request.trace_id:
        return request
    return replace(request, trace_id=new_trace_id())
