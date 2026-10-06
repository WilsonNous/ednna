from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ednna.infrastructure.database import connect_mysql
from ednna.settings import DatabaseSettings


@dataclass(frozen=True)
class MigrationDefinition:
    version: str
    filename: str
    description: str


@dataclass(frozen=True)
class MigrationStatus:
    version: str
    filename: str
    description: str
    applied: bool


class MigrationCatalog:
    def __init__(self, manifest_path: str | Path) -> None:
        raw = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        self._migrations = tuple(
            MigrationDefinition(
                version=str(item["version"]),
                filename=str(item["filename"]),
                description=str(item.get("description", "")),
            )
            for item in raw.get("migrations", [])
        )

    def list(self) -> tuple[MigrationDefinition, ...]:
        return self._migrations


class MigrationStatusService:
    """Read migration state. This service never executes migration SQL."""

    def __init__(
        self,
        settings: DatabaseSettings,
        catalog: MigrationCatalog,
    ) -> None:
        self._settings = settings
        self._catalog = catalog

    def status(self) -> tuple[MigrationStatus, ...]:
        applied = self._applied_versions()
        return tuple(
            MigrationStatus(
                version=migration.version,
                filename=migration.filename,
                description=migration.description,
                applied=migration.version in applied,
            )
            for migration in self._catalog.list()
        )

    def pending(self) -> tuple[MigrationStatus, ...]:
        return tuple(item for item in self.status() if not item.applied)

    def _applied_versions(self) -> set[str]:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Migration database is unavailable")

        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT version
                FROM orchestration_schema_migrations
                ORDER BY version
                """
            )
            return {str(row[0]) for row in cursor.fetchall()}
        finally:
            cursor.close()
            connection.close()
