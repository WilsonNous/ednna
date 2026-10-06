from ednna.infrastructure.migrations import (
    MigrationCatalog,
    MigrationDefinition,
    MigrationStatusService,
)


class FakeCatalog(MigrationCatalog):
    def __init__(self):
        self._items = (
            MigrationDefinition("000", "000.sql", "registry"),
            MigrationDefinition("001", "001.sql", "governance"),
        )

    def list(self):
        return self._items


class FakeStatusService(MigrationStatusService):
    def __init__(self):
        self._catalog = FakeCatalog()

    def _applied_versions(self):
        return {"000"}


def test_migration_status_reports_pending_without_executing_sql():
    service = FakeStatusService()

    status = service.status()
    pending = service.pending()

    assert status[0].applied is True
    assert status[1].applied is False
    assert [item.version for item in pending] == ["001"]
