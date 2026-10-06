from ednna.events.contracts import IntelligenceEvent
from ednna.events.outbox import InMemoryOutboxStore
from ednna.events.publisher import OutboxDispatcher


class FakePublisher:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)


class FailingPublisher:
    def publish(self, event):
        raise RuntimeError("broker unavailable")


def make_event():
    return IntelligenceEvent.create(
        event_type="edi.issue.blocked",
        source="eddy",
        trace_id="trace-1",
        tenant_id="netunna",
        subject="issue-123",
    )


def test_outbox_dispatch_marks_successful_delivery():
    outbox = InMemoryOutboxStore()
    event = make_event()
    outbox.enqueue(event)
    publisher = FakePublisher()

    delivered, failed = OutboxDispatcher(outbox, publisher).dispatch()

    assert delivered == 1
    assert failed == 0
    assert publisher.events == [event]
    assert outbox.pending() == ()


def test_outbox_keeps_failed_event_pending_for_retry():
    outbox = InMemoryOutboxStore()
    event = make_event()
    outbox.enqueue(event)

    delivered, failed = OutboxDispatcher(outbox, FailingPublisher()).dispatch()

    assert delivered == 0
    assert failed == 1
    pending = outbox.pending()
    assert len(pending) == 1
    assert pending[0].attempts == 1
    assert pending[0].last_error_type == "RuntimeError"
