from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ednna.infrastructure.migrations import MigrationCatalog, MigrationStatusService
from ednna.observability.readiness import ReadinessChecker, ReadinessReport
from ednna.settings import DatabaseSettings


class MigrationStatusProvider(Protocol):
    def pending(self):
        ...


@dataclass(frozen=True)
class ReleaseGateResult:
    ready: bool
    readiness: ReadinessReport
    pending_migrations: tuple[str, ...]


class ReleaseGate:
    """Read-only release gate. It never changes configuration or database state."""

    def __init__(
        self,
        readiness: ReadinessChecker,
        migrations: MigrationStatusProvider | None = None,
    ) -> None:
        self._readiness = readiness
        self._migrations = migrations

    def evaluate(self) -> ReleaseGateResult:
        readiness_report = self._readiness.check()
        pending_migrations: tuple[str, ...] = ()

        if self._migrations is not None:
            pending_migrations = tuple(
                migration.filename
                for migration in self._migrations.pending()
            )

        return ReleaseGateResult(
            ready=readiness_report.ready and not pending_migrations,
            readiness=readiness_report,
            pending_migrations=pending_migrations,
        )


def _enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def _requires_database_migrations() -> bool:
    return any(
        _enabled(flag)
        for flag in (
            "APPROVAL_API_ENABLED",
            "ACTION_API_ENABLED",
            "EVENT_INGRESS_API_ENABLED",
            "SERVICEBUS_OUTBOX_ENABLED",
            "SERVICEBUS_CONSUMER_ENABLED",
        )
    )


def build_release_gate() -> ReleaseGate:
    migrations = None
    if _requires_database_migrations():
        manifest = Path(__file__).resolve().parents[2] / "migrations" / "manifest.json"
        migrations = MigrationStatusService(
            DatabaseSettings.from_env(),
            MigrationCatalog(manifest),
        )

    return ReleaseGate(ReadinessChecker(), migrations)


def main() -> int:
    result = build_release_gate().evaluate()

    print(f"EDNNA release gate: {'READY' if result.ready else 'BLOCKED'}")

    for check in result.readiness.checks:
        status = "ready" if check.ready else "not-ready"
        print(f"- {check.component}: {status}")

    if result.pending_migrations:
        print("- pending migrations:")
        for filename in result.pending_migrations:
            print(f"  - {filename}")

    return 0 if result.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
