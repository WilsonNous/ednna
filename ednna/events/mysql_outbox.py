from __future__ import annotations

import json
from datetime import datetime, timezone

from ednna.infrastructure.database import connect_mysql
from ednna.settings import DatabaseSettings

from .contracts import IntelligenceEvent
from .outbox import OutboxRecord


class MySQLOutboxStore:
    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings

    def enqueue(self, event: IntelligenceEvent) -> None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Outbox database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO orchestration_event_outbox (
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
        finally:
            cursor.close()
            connection.close()

    def pending(self, limit: int = 100) -> tuple[OutboxRecord, ...]:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Outbox database is unavailable")
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT *
                FROM orchestration_event_outbox
                WHERE delivery_status = 'pending'
                  AND available_at <= CURRENT_TIMESTAMP(6)
                ORDER BY occurred_at ASC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return tuple(self._record(row) for row in rows)
        finally:
            cursor.close()
            connection.close()

    def mark_delivered(self, event_id: str) -> None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Outbox database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE orchestration_event_outbox
                SET delivery_status = 'delivered',
                    attempts = attempts + 1,
                    delivered_at = CURRENT_TIMESTAMP(6),
                    last_error_type = NULL
                WHERE event_id = %s
                """,
                (event_id,),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def mark_failed(self, event_id: str, error_type: str) -> None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Outbox database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE orchestration_event_outbox
                SET attempts = attempts + 1,
                    last_error_type = %s
                WHERE event_id = %s
                """,
                (error_type, event_id),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _record(row: dict) -> OutboxRecord:
        raw_data = row["data_json"]
        data = raw_data if isinstance(raw_data, dict) else json.loads(raw_data)
        occurred_at = row["occurred_at"]
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)

        event = IntelligenceEvent(
            event_id=row["event_id"],
            event_type=row["event_type"],
            source=row["source"],
            trace_id=row["trace_id"],
            tenant_id=row["tenant_id"],
            subject=row["subject"],
            occurred_at=occurred_at,
            data=data,
        )
        return OutboxRecord(
            event=event,
            delivery_status=row["delivery_status"],
            attempts=row["attempts"],
            available_at=row["available_at"],
            delivered_at=row["delivered_at"],
            last_error_type=row["last_error_type"],
        )
