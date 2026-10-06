from ednna.bootstrap import build_availability_store
from ednna.specialists.availability import (
    SpecialistAvailability,
    SpecialistAvailabilityRegistry,
)
from ednna.specialists.mysql_availability import MySQLSpecialistAvailabilityStore
from ednna.settings import DatabaseSettings


class FakeCursor:
    def __init__(self, row=None):
        self.row = row
        self.executions = []
        self.closed = False

    def execute(self, sql, params=None):
        self.executions.append((sql, params))

    def fetchone(self):
        return self.row

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, row=None):
        self.row = row
        self.cursors = []
        self.commits = 0
        self.closed = False

    def cursor(self, **kwargs):
        cursor = FakeCursor(self.row)
        self.cursors.append(cursor)
        return cursor

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def settings():
    return DatabaseSettings(
        host="db",
        user="user",
        password="password",
        database="ednna",
    )


def test_mysql_availability_store_upserts_state(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(
        "ednna.specialists.mysql_availability.connect_mysql",
        lambda _settings: connection,
    )
    store = MySQLSpecialistAvailabilityStore(settings())

    store.set(
        "eddy",
        SpecialistAvailability.DEGRADED,
        reason_code="remote_degraded",
    )

    assert connection.commits == 1
    _, params = connection.cursors[0].executions[0]
    assert params == ("eddy", "degraded", "remote_degraded")


def test_mysql_availability_store_reads_state(monkeypatch):
    connection = FakeConnection(
        {
            "specialist_id": "eddy",
            "status": "ready",
            "reason_code": None,
        }
    )
    monkeypatch.setattr(
        "ednna.specialists.mysql_availability.connect_mysql",
        lambda _settings: connection,
    )
    store = MySQLSpecialistAvailabilityStore(settings())

    state = store.get("eddy")

    assert state.status is SpecialistAvailability.READY
    assert store.is_routable("eddy") is True


def test_build_availability_store_defaults_to_memory(monkeypatch):
    monkeypatch.setenv("SPECIALIST_AVAILABILITY_DURABLE", "false")

    store = build_availability_store()

    assert isinstance(store, SpecialistAvailabilityRegistry)


def test_build_availability_store_can_select_mysql(monkeypatch):
    monkeypatch.setenv("SPECIALIST_AVAILABILITY_DURABLE", "true")
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("DB_NAME", "ednna")

    store = build_availability_store()

    assert isinstance(store, MySQLSpecialistAvailabilityStore)
