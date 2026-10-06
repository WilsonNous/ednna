from ednna.events.contracts import IntelligenceEvent
from ednna.events.router import EventRouter
from ednna.events.service import EventService
from ednna.events.store import InMemoryEventStore


def test_event_service_persists_and_routes_event():
    store = InMemoryEventStore()
    router = EventRouter()
    received = []
    router.subscribe("edi.issue.blocked", received.append)
    service = EventService(store, router)

    event = IntelligenceEvent.create(
        event_type="edi.issue.blocked",
        source="eddy",
        trace_id="trace-1",
        tenant_id="netunna",
        subject="issue-123",
        data={"reason": "manual decision required"},
    )

    handled = service.publish(event)

    assert handled == 1
    assert received == [event]
    assert store.list_by_trace("trace-1") == (event,)


def test_unknown_event_is_still_persisted_without_side_effects():
    store = InMemoryEventStore()
    router = EventRouter()
    service = EventService(store, router)

    event = IntelligenceEvent.create(
        event_type="unknown.event",
        source="test",
        trace_id="trace-2",
    )

    handled = service.publish(event)

    assert handled == 0
    assert store.list_by_trace("trace-2") == (event,)
