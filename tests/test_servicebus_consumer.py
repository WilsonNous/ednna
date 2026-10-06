import json
from datetime import datetime, timezone

from ednna.events.servicebus_consumer import AzureServiceBusConsumer


class FakeMessage:
    def __init__(self, payload, delivery_count=0):
        self.body = [json.dumps(payload).encode("utf-8")]
        self.delivery_count = delivery_count


class FakeReceiver:
    def __init__(self, messages):
        self._messages = messages
        self.completed = []
        self.abandoned = []
        self.dead_lettered = []

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

    def dead_letter_message(self, message, reason, error_description):
        self.dead_lettered.append((message, reason, error_description))


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


def build_consumer(receiver, service, max_delivery_attempts=5):
    return AzureServiceBusConsumer(
        fully_qualified_namespace="example.servicebus.windows.net",
        topic_name="ednna-events",
        subscription_name="ednna",
        event_service=service,
        credential=object(),
        client=FakeClient(receiver),
        max_delivery_attempts=max_delivery_attempts,
    )


def test_consumer_completes_message_after_successful_internal_publish():
    receiver = FakeReceiver([FakeMessage(make_payload())])
    service = CaptureEventService()

    processed, failed, dead_lettered = build_consumer(receiver, service).receive_once()

    assert processed == 1
    assert failed == 0
    assert dead_lettered == 0
    assert len(service.events) == 1
    assert len(receiver.completed) == 1
    assert receiver.abandoned == []


def test_consumer_abandons_invalid_message_before_retry_limit():
    receiver = FakeReceiver([FakeMessage({"invalid": True}, delivery_count=2)])
    service = CaptureEventService()

    processed, failed, dead_lettered = build_consumer(
        receiver,
        service,
        max_delivery_attempts=5,
    ).receive_once()

    assert processed == 0
    assert failed == 1
    assert dead_lettered == 0
    assert receiver.completed == []
    assert len(receiver.abandoned) == 1


def test_consumer_dead_letters_after_retry_limit_without_sensitive_error():
    receiver = FakeReceiver([FakeMessage({"invalid": True}, delivery_count=5)])
    service = CaptureEventService()

    processed, failed, dead_lettered = build_consumer(
        receiver,
        service,
        max_delivery_attempts=5,
    ).receive_once()

    assert processed == 0
    assert failed == 0
    assert dead_lettered == 1
    assert receiver.abandoned == []
    assert len(receiver.dead_lettered) == 1
    _, reason, description = receiver.dead_lettered[0]
    assert reason == "ProcessingFailure"
    assert description == "KeyError"
