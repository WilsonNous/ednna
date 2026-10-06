from __future__ import annotations

from pathlib import Path

from ednna.infrastructure.migrations import MigrationCatalog, MigrationStatusService
from ednna.settings import DatabaseSettings


def main() -> int:
    manifest = Path(__file__).resolve().parents[2] / "migrations" / "manifest.json"
    service = MigrationStatusService(
        DatabaseSettings.from_env(),
        MigrationCatalog(manifest),
    )

    pending = service.pending()
    if not pending:
        print("All orchestration migrations are applied.")
        return 0

    print("Pending orchestration migrations:")
    for migration in pending:
        print(f"- {migration.version} {migration.filename}: {migration.description}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
