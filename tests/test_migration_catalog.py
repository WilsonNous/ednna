import json

from ednna.infrastructure.migrations import MigrationCatalog


def test_migration_catalog_preserves_manifest_order(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "migrations": [
                    {"version": "000", "filename": "000.sql", "description": "registry"},
                    {"version": "001", "filename": "001.sql", "description": "governance"},
                ]
            }
        ),
        encoding="utf-8",
    )

    catalog = MigrationCatalog(path)

    assert [item.version for item in catalog.list()] == ["000", "001"]
    assert catalog.list()[1].filename == "001.sql"
