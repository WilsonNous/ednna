from __future__ import annotations

import os
from pathlib import Path

from ednna.orchestration.gateway import SpecialistClient
from ednna.orchestration.registry import SpecialistRegistry

from .http_client import HttpSpecialistClient
from .manifest import SpecialistManifest, load_specialist_manifests


def load_catalog_from_env() -> tuple[SpecialistManifest, ...]:
    path = os.getenv("SPECIALIST_MANIFEST_PATH", "").strip()
    if not path:
        return ()
    return load_specialist_manifests(Path(path))


def register_catalog(
    registry: SpecialistRegistry,
    manifests: tuple[SpecialistManifest, ...],
) -> None:
    for manifest in manifests:
        registry.register(manifest.descriptor)


def build_manifest_clients(
    manifests: tuple[SpecialistManifest, ...],
) -> dict[str, SpecialistClient]:
    clients: dict[str, SpecialistClient] = {}

    for manifest in manifests:
        transport = manifest.transport
        if transport is None:
            continue

        base_url = os.getenv(transport.base_url_env, "").strip()
        api_token = os.getenv(transport.api_token_env, "").strip()
        if not base_url or not api_token:
            continue

        timeout = 10.0
        if transport.timeout_env:
            timeout = float(os.getenv(transport.timeout_env, "10"))

        clients[manifest.descriptor.specialist_id] = HttpSpecialistClient(
            specialist_id=manifest.descriptor.specialist_id,
            base_url=base_url,
            api_token=api_token,
            timeout_seconds=timeout,
        )

    return clients
