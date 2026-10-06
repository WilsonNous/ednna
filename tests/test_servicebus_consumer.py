import json
from datetime import datetime, timezone

from ednna.events.servicebus_consumer import AzureServiceBusConsumer


class FakeMessage:
    def __init__(self, payload):
        self.body = [json.dumps(payload).encode("utf-8")]


class FakeReceiver:
    def __init__(self, messages):
        self._messages = messages
        self.completed = []
        self.abandoned = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def receive_messages(self, max_message_count, max_wait_time):
        return self._messages

    def complete_message(self, message):
        self.completed.append(message)

    def abandon_message(self, message):
        self.abandoned.append(message)


class FakeClient:
    def __init__(self, receiver):
        self.receiver = receiver

    def get_subscription_receiver(self, **kwargs):
        return self.receiver


class CaptureEventService:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)
        return 0


def make_payload():
    return {
        "event_id": "event-1",
        "event_type": "edi.operation.approval_required",
        "source": "eddy",
        "trace_id": "trace-1",
        "tenant_id": "tenant-1",
        "subject": "issue-123",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "data": {"reason": "manual review"},
    }


def test_consumer_completes_message_after_successful_internal_publish():
    receiver = FakeReceiver([FakeMessage(make_payload())])
    service = CaptureEventService()
    consumer = AzureServiceBusConsumer(
        fully_qualified_namespace="example.servicebus.windows.net",
        topic_name="ednna-events",
        subscription_name="ednna",
        event_service=service,
        credential=object(),
        client=FakeClient(receiver),
    )

    processed, failed = consumer.receive_once()

    assert processed == 1
    assert failed == 0
    assert len(service.events) == 1
    assert len(receiver.completed) == 1
    assert receiver.abandoned == []


def test_consumer_abandons_invalid_message():
    receiver = FakeReceiver([FakeMessage({"invalid": True})])
    service = CaptureEventService()
    consumer = AzureServiceBusConsumer(
        fully_qualified_namespace="example.servicebus.windows.net",
        topic_name="ednna-events",
        subscription_name="ednna",
        event_service=service,
        credential=object(),
        client=FakeClient(receiver),
    )

    processed, failed = consumer.receive_once()

    assert processed == 0
    assert failed == 1
    assert receiver.completed == []
    assert len(receiver.abandoned) == 1
