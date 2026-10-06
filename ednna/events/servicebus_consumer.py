from __future__ import annotations

import json
import os
from datetime import datetime

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.servicebus import ServiceBusClient

from .contracts import IntelligenceEvent
from .service import EventService


class AzureServiceBusConsumer:
    def __init__(
        self,
        fully_qualified_namespace: str,
        topic_name: str,
        subscription_name: str,
        event_service: EventService,
        credential=None,
        client: ServiceBusClient | None = None,
        max_delivery_attempts: int = 5,
    ) -> None:
        self._topic_name = topic_name
        self._subscription_name = subscription_name
        self._event_service = event_service
        self._credential = credential or self._build_credential()
        self._client = client or ServiceBusClient(
            fully_qualified_namespace=fully_qualified_namespace,
            credential=self._credential,
        )
        self._max_delivery_attempts = max_delivery_attempts

    def receive_once(
        self,
        max_message_count: int = 50,
        max_wait_time: int = 5,
    ) -> tuple[int, int, int]:
        processed = 0
        failed = 0
        dead_lettered = 0

        with self._client.get_subscription_receiver(
            topic_name=self._topic_name,
            subscription_name=self._subscription_name,
            max_wait_time=max_wait_time,
        ) as receiver:
            messages = receiver.receive_messages(
                max_message_count=max_message_count,
                max_wait_time=max_wait_time,
            )

            for message in messages:
                try:
                    event = self._to_event(message)
                    self._event_service.publish(event)
                except Exception as exc:
                    delivery_count = int(getattr(message, "delivery_count", 0) or 0)
                    if delivery_count >= self._max_delivery_attempts:
                        receiver.dead_letter_message(
                            message,
                            reason="ProcessingFailure",
                            error_description=type(exc).__name__,
                        )
                        dead_lettered += 1
                    else:
                        receiver.abandon_message(message)
                        failed += 1
                    continue

                receiver.complete_message(message)
                processed += 1

        return processed, failed, dead_lettered

    @staticmethod
    def _to_event(message) -> IntelligenceEvent:
        body = b"".join(message.body).decode("utf-8")
        payload = json.loads(body)

        occurred_at = datetime.fromisoformat(
            str(payload["occurred_at"]).replace("Z", "+00:00")
        )

        return IntelligenceEvent(
            event_id=str(payload["event_id"]),
            event_type=str(payload["event_type"]),
            source=str(payload["source"]),
            trace_id=str(payload["trace_id"]),
            tenant_id=payload.get("tenant_id"),
            subject=payload.get("subject"),
            occurred_at=occurred_at,
            data=payload.get("data", {}),
        )

    @staticmethod
    def _build_credential():
        client_id = os.getenv("SERVICEBUS_MANAGED_IDENTITY_CLIENT_ID", "").strip()
        if client_id:
            return ManagedIdentityCredential(client_id=client_id)
        return DefaultAzureCredential()


def build_servicebus_consumer(event_service: EventService) -> AzureServiceBusConsumer:
    namespace = os.getenv("SERVICEBUS_NAMESPACE", "").strip()
    topic = os.getenv("SERVICEBUS_TOPIC", "").strip()
    subscription = os.getenv("SERVICEBUS_SUBSCRIPTION", "").strip()
    max_delivery_attempts = int(os.getenv("SERVICEBUS_MAX_DELIVERY_ATTEMPTS", "5"))

    if not namespace or not topic or not subscription:
        raise RuntimeError(
            "SERVICEBUS_NAMESPACE, SERVICEBUS_TOPIC and SERVICEBUS_SUBSCRIPTION are required"
        )

    return AzureServiceBusConsumer(
        fully_qualified_namespace=namespace,
        topic_name=topic,
        subscription_name=subscription,
        event_service=event_service,
        max_delivery_attempts=max_delivery_attempts,
    )
