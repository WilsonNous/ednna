from __future__ import annotations

from datetime import timezone

from mysql.connector import IntegrityError

from ednna.infrastructure.database import connect_mysql
from ednna.settings import DatabaseSettings

from .action_ledger import (
    ActionExecutionNotFoundError,
    ActionExecutionNotReconcilableError,
    ActionExecutionRecord,
    ActionExecutionStatus,
    DuplicateActionExecutionError,
)


class MySQLActionExecutionLedger:
    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings

    def get(self, idempotency_key: str) -> ActionExecutionRecord | None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Action ledger database is unavailable")
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT *
                FROM orchestration_action_executions
                WHERE idempotency_key = %s
                """,
                (idempotency_key,),
            )
            row = cursor.fetchone()
            return self._row_to_record(row) if row is not None else None
        finally:
            cursor.close()
            connection.close()

    def start(
        self,
        idempotency_key: str,
        trace_id: str,
        capability: str,
        tenant_id: str | None = None,
        requested_by: str | None = None,
    ) -> ActionExecutionRecord:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Action ledger database is unavailable")
        cursor = connection.cursor()
        try:
            try:
                cursor.execute(
                    """
                    INSERT INTO orchestration_action_executions (
                        idempotency_key, trace_id, capability, tenant_id,
                        requested_by, status, started_at
                    ) VALUES (%s, %s, %s, %s, %s, 'started', CURRENT_TIMESTAMP(6))
                    """,
                    (
                        idempotency_key,
                        trace_id,
                        capability,
                        tenant_id,
                        requested_by,
                    ),
                )
                connection.commit()
            except IntegrityError as exc:
                connection.rollback()
                raise DuplicateActionExecutionError(idempotency_key) from exc
        finally:
            cursor.close()
            connection.close()

        return self._get_required(idempotency_key)

    def succeed(
        self,
        idempotency_key: str,
        specialist_id: str,
        response_status: str,
        evidence_count: int,
    ) -> ActionExecutionRecord:
        self._update(
            idempotency_key,
            """
            UPDATE orchestration_action_executions
            SET status = 'succeeded',
                completed_at = CURRENT_TIMESTAMP(6),
                specialist_id = %s,
                response_status = %s,
                evidence_count = %s,
                error_type = NULL
            WHERE idempotency_key = %s
            """,
            (
                specialist_id,
                response_status,
                evidence_count,
                idempotency_key,
            ),
        )
        return self._get_required(idempotency_key)

    def uncertain(
        self,
        idempotency_key: str,
        error_type: str,
    ) -> ActionExecutionRecord:
        self._update(
            idempotency_key,
            """
            UPDATE orchestration_action_executions
            SET status = 'uncertain',
                completed_at = CURRENT_TIMESTAMP(6),
                error_type = %s
            WHERE idempotency_key = %s
            """,
            (error_type, idempotency_key),
        )
        return self._get_required(idempotency_key)

    def reconcile(
        self,
        idempotency_key: str,
        status: ActionExecutionStatus,
        reconciled_by: str,
        note: str,
        reference: str,
    ) -> ActionExecutionRecord:
        allowed = {
            ActionExecutionStatus.RECONCILED_SUCCEEDED,
            ActionExecutionStatus.RECONCILED_NOT_EXECUTED,
        }
        if status not in allowed:
            raise ActionExecutionNotReconcilableError(idempotency_key)

        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Action ledger database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE orchestration_action_executions
                SET status = %s,
                    reconciled_at = CURRENT_TIMESTAMP(6),
                    reconciled_by = %s,
                    reconciliation_note = %s,
                    reconciliation_reference = %s
                WHERE idempotency_key = %s
                  AND status = 'uncertain'
                """,
                (
                    status.value,
                    reconciled_by,
                    note,
                    reference,
                    idempotency_key,
                ),
            )
            if cursor.rowcount == 0:
                connection.rollback()
                current = self.get(idempotency_key)
                if current is None:
                    raise ActionExecutionNotFoundError(idempotency_key)
                raise ActionExecutionNotReconcilableError(idempotency_key)
            connection.commit()
        finally:
            cursor.close()
            connection.close()

        return self._get_required(idempotency_key)

    def _update(self, idempotency_key: str, sql: str, params: tuple) -> None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Action ledger database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            if cursor.rowcount == 0:
                raise ActionExecutionNotFoundError(idempotency_key)
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def _get_required(self, idempotency_key: str) -> ActionExecutionRecord:
        record = self.get(idempotency_key)
        if record is None:
            raise ActionExecutionNotFoundError(idempotency_key)
        return record

    @staticmethod
    def _row_to_record(row: dict) -> ActionExecutionRecord:
        started_at = row["started_at"]
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        completed_at = row["completed_at"]
        if completed_at is not None and completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)

        reconciled_at = row.get("reconciled_at")
        if reconciled_at is not None and reconciled_at.tzinfo is None:
            reconciled_at = reconciled_at.replace(tzinfo=timezone.utc)

        return ActionExecutionRecord(
            idempotency_key=row["idempotency_key"],
            trace_id=row["trace_id"],
            capability=row["capability"],
            tenant_id=row["tenant_id"],
            requested_by=row["requested_by"],
            status=ActionExecutionStatus(row["status"]),
            started_at=started_at,
            completed_at=completed_at,
            specialist_id=row["specialist_id"],
            response_status=row["response_status"],
            evidence_count=row["evidence_count"],
            error_type=row["error_type"],
            reconciled_at=reconciled_at,
            reconciled_by=row.get("reconciled_by"),
            reconciliation_note=row.get("reconciliation_note"),
            reconciliation_reference=row.get("reconciliation_reference"),
        )
