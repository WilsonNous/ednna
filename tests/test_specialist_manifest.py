import json

from ednna.orchestration.discovery import CapabilityDiscovery
from ednna.orchestration.planner import Planner
from ednna.orchestration.registry import SpecialistRegistry
from ednna.specialists.eddy import EDDY_DESCRIPTOR
from ednna.specialists.manifest import load_specialist_manifests


def test_manifest_loads_specialist_descriptor(tmp_path):
    path = tmp_path / "specialists.json"
    path.write_text(
        json.dumps(
            {
                "specialists": [
                    {
                        "specialist_id": "finance",
                        "name": "Finance",
                        "domain": "finance",
                        "description": "Especialista financeiro",
                        "capabilities": [
                            {
                                "name": "finance.exposure.get",
                                "kind": "query",
                                "description": "Consultar exposição financeira do cliente",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    manifests = load_specialist_manifests(path)

    assert len(manifests) == 1
    assert manifests[0].descriptor.specialist_id == "finance"
    assert manifests[0].descriptor.capabilities[0].name == "finance.exposure.get"


def test_planner_can_combine_multiple_specialists_from_catalog(tmp_path):
    path = tmp_path / "specialists.json"
    path.write_text(
        json.dumps(
            {
                "specialists": [
                    {
                        "specialist_id": "finance",
                        "name": "Finance",
                        "domain": "finance",
                        "description": "Especialista financeiro",
                        "capabilities": [
                            {
                                "name": "finance.exposure.get",
                                "kind": "query",
                                "description": "Consultar exposição financeira do cliente",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    for manifest in load_specialist_manifests(path):
        registry.register(manifest.descriptor)

    planner = Planner(CapabilityDiscovery(registry), minimum_score=1.0, maximum_steps=3)
    plan = planner.plan("estado geral da operação EDI e exposição financeira do cliente")

    specialist_ids = {step.specialist_id for step in plan.steps}
    assert "eddy" in specialist_ids
    assert "finance" in specialist_ids
