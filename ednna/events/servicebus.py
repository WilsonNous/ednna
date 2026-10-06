from __future__ import annotations

import json
import os
from dataclasses import asdict

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

from .contracts import IntelligenceEvent


class AzureServiceBusPublisher:
    def __init__(
        self,
        fully_qualified_namespace: str,
        topic_name: str,
        credential=None,
        client: ServiceBusClient | None = None,
    ) -> None:
        self._topic_name = topic_name
        self._credential = credential or self._build_credential()
        self._client = client or ServiceBusClient(
            fully_qualified_namespace=fully_qualified_namespace,
            credential=self._credential,
        )

    def publish(self, event: IntelligenceEvent) -> None:
        payload = asdict(event)
        payload["occurred_at"] = event.occurred_at.isoformat()

        message = ServiceBusMessage(
            json.dumps(payload, ensure_ascii=False),
            message_id=event.event_id,
            subject=event.event_type,
            correlation_id=event.trace_id,
            application_properties={
                "source": event.source,
                "tenant_id": event.tenant_id or "",
            },
        )

        with self._client.get_topic_sender(topic_name=self._topic_name) as sender:
            sender.send_messages(message)

    @staticmethod
    def _build_credential():
        client_id = os.getenv("SERVICEBUS_MANAGED_IDENTITY_CLIENT_ID", "").strip()
        if client_id:
            return ManagedIdentityCredential(client_id=client_id)
        return DefaultAzureCredential()


def build_servicebus_publisher() -> AzureServiceBusPublisher:
    namespace = os.getenv("SERVICEBUS_NAMESPACE", "").strip()
    topic = os.getenv("SERVICEBUS_TOPIC", "").strip()
    if not namespace or not topic:
        raise RuntimeError("SERVICEBUS_NAMESPACE and SERVICEBUS_TOPIC are required")

    return AzureServiceBusPublisher(
        fully_qualified_namespace=namespace,
        topic_name=topic,
    )
