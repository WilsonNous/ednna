from __future__ import annotations

import json
from datetime import timezone

from mysql.connector import IntegrityError

from ednna.infrastructure.database import connect_mysql
from ednna.settings import DatabaseSettings

from .contracts import IntelligenceEvent


class DuplicateEventError(RuntimeError):
    pass


class MySQLEventStore:
    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings

    def append(self, event: IntelligenceEvent) -> None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Event inbox database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO orchestration_event_inbox (
                    event_id, event_type, source, trace_id, tenant_id,
                    subject, occurred_at, data_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event.event_id,
                    event.event_type,
                    event.source,
                    event.trace_id,
                    event.tenant_id,
                    event.subject,
                    event.occurred_at.replace(tzinfo=None),
                    json.dumps(event.data, ensure_ascii=False),
                ),
            )
            connection.commit()
        except IntegrityError as exc:
            connection.rollback()
            raise DuplicateEventError(
                f"Duplicate event blocked for event_id '{event.event_id}'"
            ) from exc
        finally:
            cursor.close()
            connection.close()

    def list_by_trace(self, trace_id: str) -> tuple[IntelligenceEvent, ...]:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Event inbox database is unavailable")
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT event_id, event_type, source, trace_id, tenant_id,
                       subject, occurred_at, data_json
                FROM orchestration_event_inbox
                WHERE trace_id = %s
                ORDER BY received_at ASC
                """,
                (trace_id,),
            )
            rows = cursor.fetchall()
            events = []
            for row in rows:
                occurred_at = row["occurred_at"]
                if occurred_at.tzinfo is None:
                    occurred_at = occurred_at.replace(tzinfo=timezone.utc)
                raw_data = row["data_json"]
                data = raw_data if isinstance(raw_data, dict) else json.loads(raw_data)
                events.append(
                    IntelligenceEvent(
                        event_id=row["event_id"],
                        event_type=row["event_type"],
                        source=row["source"],
                        trace_id=row["trace_id"],
                        tenant_id=row["tenant_id"],
                        subject=row["subject"],
                        occurred_at=occurred_at,
                        data=data,
                    )
                )
            return tuple(events)
        finally:
            cursor.close()
            connection.close()
