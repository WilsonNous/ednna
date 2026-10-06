from __future__ import annotations

import os

from ednna.settings import require_env
from ednna.specialists.http_client import HttpSpecialistClient


def build_eddy_client() -> HttpSpecialistClient:
    base_url = require_env("EDDY_BASE_URL")
    api_token = require_env("EDDY_API_TOKEN")
    timeout_seconds = float(os.getenv("EDDY_TIMEOUT_SECONDS", "10"))

    return HttpSpecialistClient(
        specialist_id="eddy",
        base_url=base_url,
        api_token=api_token,
        timeout_seconds=timeout_seconds,
    )
