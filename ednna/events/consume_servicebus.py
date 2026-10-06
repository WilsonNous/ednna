from __future__ import annotations

from ednna.events.bootstrap import build_event_router
from ednna.events.consumer_feature_flags import servicebus_consumer_enabled
from ednna.events.mysql_store import MySQLEventStore
from ednna.events.service import EventService
from ednna.events.servicebus_consumer import build_servicebus_consumer
from ednna.governance.mysql_stores import MySQLApprovalStore
from ednna.settings import DatabaseSettings


def main() -> int:
    if not servicebus_consumer_enabled():
        return 0

    settings = DatabaseSettings.from_env()
    event_service = EventService(
        MySQLEventStore(settings),
        build_event_router(MySQLApprovalStore(settings)),
    )
    consumer = build_servicebus_consumer(event_service)
    _processed, failed, dead_lettered = consumer.receive_once()
    return 0 if failed == 0 and dead_lettered == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
