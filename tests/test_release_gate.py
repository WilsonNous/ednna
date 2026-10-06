from dataclasses import dataclass

from ednna.observability.readiness import ReadinessCheck, ReadinessReport
from ednna.operations.release_gate import ReleaseGate


class FakeReadiness:
    def __init__(self, ready=True):
        self._ready = ready

    def check(self):
        return ReadinessReport(
            ready=self._ready,
            checks=(
                ReadinessCheck(
                    component="application",
                    ready=self._ready,
                    reason=None if self._ready else "missing",
                ),
            ),
        )


@dataclass(frozen=True)
class FakeMigration:
    filename: str


class FakeMigrations:
    def __init__(self, filenames=()):
        self._filenames = filenames

    def pending(self):
        return tuple(FakeMigration(filename) for filename in self._filenames)


def test_release_gate_passes_when_readiness_and_migrations_are_clear():
    result = ReleaseGate(
        FakeReadiness(True),
        FakeMigrations(()),
    ).evaluate()

    assert result.ready is True
    assert result.pending_migrations == ()


def test_release_gate_blocks_on_readiness_failure():
    result = ReleaseGate(
        FakeReadiness(False),
        FakeMigrations(()),
    ).evaluate()

    assert result.ready is False


def test_release_gate_blocks_on_pending_migrations():
    result = ReleaseGate(
        FakeReadiness(True),
        FakeMigrations(("003_event_outbox.sql",)),
    ).evaluate()

    assert result.ready is False
    assert result.pending_migrations == ("003_event_outbox.sql",)
