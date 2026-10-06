from __future__ import annotations

import re
from dataclasses import dataclass

from .manifest import SpecialistManifest


_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
_ENV_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True)
class ConformanceIssue:
    code: str
    message: str


@dataclass(frozen=True)
class ConformanceReport:
    specialist_id: str
    valid: bool
    issues: tuple[ConformanceIssue, ...]


class SpecialistConformanceValidator:
    """Validate a specialist manifest before it enters the EDNNA registry."""

    def validate(self, manifest: SpecialistManifest) -> ConformanceReport:
        descriptor = manifest.descriptor
        issues: list[ConformanceIssue] = []

        if not _ID_PATTERN.fullmatch(descriptor.specialist_id):
            issues.append(
                ConformanceIssue(
                    "invalid_specialist_id",
                    "specialist_id must use lowercase letters, numbers, '_' or '-'",
                )
            )

        if not _ID_PATTERN.fullmatch(descriptor.domain):
            issues.append(
                ConformanceIssue(
                    "invalid_domain",
                    "domain must use lowercase letters, numbers, '_' or '-'",
                )
            )

        if not descriptor.capabilities:
            issues.append(
                ConformanceIssue(
                    "missing_capabilities",
                    "specialist must declare at least one capability",
                )
            )

        seen: set[str] = set()
        for capability in descriptor.capabilities:
            if capability.name in seen:
                issues.append(
                    ConformanceIssue(
                        "duplicate_capability",
                        f"duplicate capability '{capability.name}'",
                    )
                )
            seen.add(capability.name)

            parts = capability.name.split(".")
            if len(parts) < 3 or any(not part for part in parts):
                issues.append(
                    ConformanceIssue(
                        "invalid_capability_name",
                        f"capability '{capability.name}' must have at least 3 segments",
                    )
                )
            elif parts[0] != descriptor.domain:
                issues.append(
                    ConformanceIssue(
                        "capability_domain_mismatch",
                        f"capability '{capability.name}' must start with '{descriptor.domain}.'",
                    )
                )

            if not capability.description.strip():
                issues.append(
                    ConformanceIssue(
                        "missing_capability_description",
                        f"capability '{capability.name}' needs a description",
                    )
                )

        if manifest.transport is not None:
            env_names = (
                manifest.transport.base_url_env,
                manifest.transport.api_token_env,
                manifest.transport.timeout_env,
            )
            for env_name in env_names:
                if env_name and not _ENV_PATTERN.fullmatch(env_name):
                    issues.append(
                        ConformanceIssue(
                            "invalid_transport_env",
                            f"transport env '{env_name}' must be uppercase snake case",
                        )
                    )

        return ConformanceReport(
            specialist_id=descriptor.specialist_id,
            valid=not issues,
            issues=tuple(issues),
        )
