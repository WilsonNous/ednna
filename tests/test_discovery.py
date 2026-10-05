from ednna.bootstrap import build_registry
from ednna.orchestration.discovery import CapabilityDiscovery


def test_discovery_finds_issue_capability_from_portuguese_description():
    discovery = CapabilityDiscovery(build_registry())

    matches = discovery.search("consultar chamado EDI")

    assert matches
    assert matches[0].capability.name == "edi.issue.inspect"
    assert matches[0].specialist_id == "eddy"


def test_discovery_returns_empty_for_unrelated_request():
    discovery = CapabilityDiscovery(build_registry())

    matches = discovery.search("previsão do tempo em Florianópolis")

    assert matches == ()
