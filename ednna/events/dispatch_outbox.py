from __future__ import annotations

from ednna.events.mysql_outbox import MySQLOutboxStore
from ednna.events.publisher import OutboxDispatcher
from ednna.events.servicebus import build_servicebus_publisher
from ednna.events.servicebus_feature_flags import servicebus_outbox_enabled
from ednna.settings import DatabaseSettings


def main() -> int:
    if not servicebus_outbox_enabled():
        return 0

    dispatcher = OutboxDispatcher(
        MySQLOutboxStore(DatabaseSettings.from_env()),
        build_servicebus_publisher(),
    )
    delivered, failed = dispatcher.dispatch(limit=100)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
