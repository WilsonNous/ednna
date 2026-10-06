from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ednna.orchestration.contracts import Capability, OperationKind, SpecialistDescriptor


@dataclass(frozen=True)
class SpecialistTransportManifest:
    base_url_env: str
    api_token_env: str
    timeout_env: str | None = None


@dataclass(frozen=True)
class SpecialistManifest:
    descriptor: SpecialistDescriptor
    transport: SpecialistTransportManifest | None = None


def load_specialist_manifests(path: str | Path) -> tuple[SpecialistManifest, ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items = raw.get("specialists", [])
    manifests: list[SpecialistManifest] = []

    for item in items:
        capabilities = tuple(
            Capability(
                name=capability["name"],
                kind=OperationKind(capability["kind"]),
                description=capability.get("description", ""),
            )
            for capability in item.get("capabilities", [])
        )

        transport_data = item.get("transport")
        transport = None
        if transport_data:
            transport = SpecialistTransportManifest(
                base_url_env=transport_data["base_url_env"],
                api_token_env=transport_data["api_token_env"],
                timeout_env=transport_data.get("timeout_env"),
            )

        manifests.append(
            SpecialistManifest(
                descriptor=SpecialistDescriptor(
                    specialist_id=item["specialist_id"],
                    name=item["name"],
                    domain=item["domain"],
                    description=item.get("description", ""),
                    capabilities=capabilities,
                ),
                transport=transport,
            )
        )

    return tuple(manifests)
