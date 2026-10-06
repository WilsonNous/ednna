import json

from ednna.events.contracts import IntelligenceEvent
from ednna.events.servicebus import AzureServiceBusPublisher


class FakeSender:
    def __init__(self):
        self.messages = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def send_messages(self, message):
        self.messages.append(message)


class FakeClient:
    def __init__(self):
        self.sender = FakeSender()
        self.topic_names = []

    def get_topic_sender(self, topic_name):
        self.topic_names.append(topic_name)
        return self.sender


def test_servicebus_publisher_uses_event_identity_and_trace():
    client = FakeClient()
    publisher = AzureServiceBusPublisher(
        fully_qualified_namespace="example.servicebus.windows.net",
        topic_name="ednna-events",
        credential=object(),
        client=client,
    )
    event = IntelligenceEvent.create(
        event_type="edi.issue.blocked",
        source="eddy",
        trace_id="trace-1",
        tenant_id="tenant-1",
        subject="issue-123",
        data={"issue_id": 123},
    )

    publisher.publish(event)

    assert client.topic_names == ["ednna-events"]
    assert len(client.sender.messages) == 1
    message = client.sender.messages[0]
    assert message.message_id == event.event_id
    assert message.correlation_id == "trace-1"
    body = b"".join(message.body).decode("utf-8")
    payload = json.loads(body)
    assert payload["event_type"] == "edi.issue.blocked"
    assert payload["tenant_id"] == "tenant-1"
