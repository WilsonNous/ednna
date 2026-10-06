from __future__ import annotations

from pathlib import Path

from ednna.infrastructure.migrations import MigrationCatalog
from ednna.settings import DatabaseSettings
from ednna.infrastructure.database import connect_mysql


def _statements(sql: str) -> tuple[str, ...]:
    return tuple(
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
    )


def apply_pending_migrations() -> tuple[str, ...]:
    root = Path(__file__).resolve().parents[2]
    migrations_dir = root / "migrations"
    catalog = MigrationCatalog(migrations_dir / "manifest.json")
    settings = DatabaseSettings.from_env()

    connection = connect_mysql(settings)
    if connection is None:
        raise RuntimeError("Migration database is unavailable")

    applied_now: list[str] = []
    cursor = connection.cursor()
    try:
        # Bootstrap the registry idempotently before reading applied versions.
        bootstrap = migrations_dir / "000_schema_migrations.sql"
        for statement in _statements(bootstrap.read_text(encoding="utf-8")):
            cursor.execute(statement)
        connection.commit()

        cursor.execute("SELECT version FROM orchestration_schema_migrations")
        applied = {str(row[0]) for row in cursor.fetchall()}

        for migration in catalog.list():
            if migration.version in applied:
                continue

            path = migrations_dir / migration.filename
            for statement in _statements(path.read_text(encoding="utf-8")):
                cursor.execute(statement)

            connection.commit()
            applied_now.append(migration.version)
            applied.add(migration.version)

        return tuple(applied_now)
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def main() -> int:
    applied = apply_pending_migrations()
    if applied:
        print("Applied orchestration migrations: " + ", ".join(applied))
    else:
        print("No pending orchestration migrations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
