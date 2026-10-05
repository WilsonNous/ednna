from __future__ import annotations

import json

from ednna.infrastructure.database import connect_mysql
from ednna.settings import DatabaseSettings

from .events import AuditEvent


class MySQLAuditStore:
    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings

    def append(self, event: AuditEvent) -> None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Audit database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO orchestration_audit_events (
                    trace_id, event_type, event_timestamp, user_id, tenant_id,
                    conversation_id, specialist_id, capability, status, confidence,
                    requires_human, details_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event.trace_id,
                    event.event_type,
                    event.timestamp.replace(tzinfo=None),
                    event.user_id,
                    event.tenant_id,
                    event.conversation_id,
                    event.specialist_id,
                    event.capability,
                    event.status,
                    event.confidence,
                    event.requires_human,
                    json.dumps(event.details, ensure_ascii=False),
                ),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def list_by_trace(self, trace_id: str) -> tuple[AuditEvent, ...]:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Audit database is unavailable")
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT trace_id, event_type, event_timestamp, user_id, tenant_id,
                       conversation_id, specialist_id, capability, status, confidence,
                       requires_human, details_json
                FROM orchestration_audit_events
                WHERE trace_id = %s
                ORDER BY id ASC
                """,
                (trace_id,),
            )
            rows = cursor.fetchall()
            return tuple(
                AuditEvent(
                    event_type=row["event_type"],
                    trace_id=row["trace_id"],
                    timestamp=row["event_timestamp"],
                    user_id=row["user_id"],
                    tenant_id=row["tenant_id"],
                    conversation_id=row["conversation_id"],
                    specialist_id=row["specialist_id"],
                    capability=row["capability"],
                    status=row["status"],
                    confidence=float(row["confidence"]) if row["confidence"] is not None else None,
                    requires_human=row["requires_human"],
                    details=row["details_json"] if isinstance(row["details_json"], dict)
                    else json.loads(row["details_json"]),
                )
                for row in rows
            )
        finally:
            cursor.close()
            connection.close()
