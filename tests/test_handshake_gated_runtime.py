from ednna.bootstrap import build_multiagent_runtime
from ednna.specialists.availability import SpecialistAvailability


def test_multiagent_runtime_preserves_legacy_behavior_when_handshake_disabled(monkeypatch):
    monkeypatch.setenv("SPECIALIST_HANDSHAKE_ENFORCED", "false")
    monkeypatch.setenv("EDDY_ENABLED", "false")
    monkeypatch.delenv("SPECIALIST_MANIFEST_PATH", raising=False)

    registry, gateway, availability = build_multiagent_runtime()

    assert registry.get_specialist("eddy") is not None
    assert gateway is not None
    assert availability is None


def test_multiagent_runtime_enforces_unknown_state_when_handshake_enabled_without_client(
    monkeypatch,
):
    monkeypatch.setenv("SPECIALIST_HANDSHAKE_ENFORCED", "true")
    monkeypatch.setenv("EDDY_ENABLED", "false")
    monkeypatch.delenv("SPECIALIST_MANIFEST_PATH", raising=False)

    registry, gateway, availability = build_multiagent_runtime()

    assert registry.get_specialist("eddy") is not None
    assert gateway is not None
    assert availability is not None
    assert availability.get("eddy").status is SpecialistAvailability.UNKNOWN
    assert availability.is_routable("eddy") is False
