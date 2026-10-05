from ednna.bootstrap import build_registry
from ednna.orchestration.discovery import CapabilityDiscovery
from ednna.orchestration.planner import Planner


def test_planner_builds_auditable_step_for_edi_status():
    planner = Planner(CapabilityDiscovery(build_registry()))

    plan = planner.plan("qual o estado geral da operação EDI")

    assert plan.steps
    assert plan.steps[0].specialist_id == "eddy"
    assert plan.steps[0].capability == "edi.status.get"


def test_planner_does_not_invent_capabilities():
    planner = Planner(CapabilityDiscovery(build_registry()))

    plan = planner.plan("qual é o faturamento do cliente")

    assert plan.steps == ()
