from __future__ import annotations

from mysql.connector import IntegrityError

from ednna.infrastructure.database import connect_mysql
from ednna.settings import DatabaseSettings

from .approvals import (
    ApprovalAlreadyBoundError,
    ApprovalNotFoundForBindingError,
    ApprovalRequest,
    ApprovalStatus,
)
from .idempotency import DuplicateActionError


class MySQLApprovalStore:
    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings

    def save(self, approval: ApprovalRequest) -> None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Approval database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO orchestration_approvals (
                    approval_id, trace_id, capability, specialist_id, tenant_id, requested_by,
                    reason, status, requested_at, decided_at, decided_by, decision_note,
                    action_idempotency_key, action_bound_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    decided_at = VALUES(decided_at),
                    decided_by = VALUES(decided_by),
                    decision_note = VALUES(decision_note)
                """,
                (
                    approval.approval_id,
                    approval.trace_id,
                    approval.capability,
                    approval.specialist_id,
                    approval.tenant_id,
                    approval.requested_by,
                    approval.reason,
                    approval.status.value,
                    approval.requested_at.replace(tzinfo=None),
                    approval.decided_at.replace(tzinfo=None) if approval.decided_at else None,
                    approval.decided_by,
                    approval.decision_note,
                    approval.action_idempotency_key,
                    (
                        approval.action_bound_at.replace(tzinfo=None)
                        if approval.action_bound_at
                        else None
                    ),
                ),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def get(self, approval_id: str) -> ApprovalRequest | None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Approval database is unavailable")
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM orchestration_approvals WHERE approval_id = %s",
                (approval_id,),
            )
            row = cursor.fetchone()
            return self._row_to_approval(row) if row is not None else None
        finally:
            cursor.close()
            connection.close()

    def bind_action(
        self,
        approval_id: str,
        idempotency_key: str,
    ) -> ApprovalRequest:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Approval database is unavailable")
        cursor = connection.cursor(dictionary=True)
        try:
            try:
                cursor.execute(
                    """
                    UPDATE orchestration_approvals
                    SET action_idempotency_key = COALESCE(action_idempotency_key, %s),
                        action_bound_at = COALESCE(action_bound_at, CURRENT_TIMESTAMP(6))
                    WHERE approval_id = %s
                      AND (
                          action_idempotency_key IS NULL
                          OR action_idempotency_key = %s
                      )
                    """,
                    (idempotency_key, approval_id, idempotency_key),
                )
            except IntegrityError as exc:
                connection.rollback()
                raise ApprovalAlreadyBoundError(
                    "Action key is already bound to another approval"
                ) from exc

            if cursor.rowcount == 0:
                cursor.execute(
                    """
                    SELECT approval_id, action_idempotency_key
                    FROM orchestration_approvals
                    WHERE approval_id = %s
                    """,
                    (approval_id,),
                )
                existing = cursor.fetchone()
                if existing is None:
                    raise ApprovalNotFoundForBindingError(approval_id)
                raise ApprovalAlreadyBoundError(
                    "Approval is already bound to another action"
                )

            connection.commit()
            cursor.execute(
                "SELECT * FROM orchestration_approvals WHERE approval_id = %s",
                (approval_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise ApprovalNotFoundForBindingError(approval_id)
            return self._row_to_approval(row)
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def _row_to_approval(row: dict) -> ApprovalRequest:
        return ApprovalRequest(
            approval_id=row["approval_id"],
            trace_id=row["trace_id"],
            capability=row["capability"],
            specialist_id=row["specialist_id"],
            reason=row["reason"],
            tenant_id=row.get("tenant_id"),
            requested_by=row.get("requested_by"),
            status=ApprovalStatus(row["status"]),
            requested_at=row["requested_at"],
            decided_at=row["decided_at"],
            decided_by=row["decided_by"],
            decision_note=row["decision_note"],
            action_idempotency_key=row.get("action_idempotency_key"),
            action_bound_at=row.get("action_bound_at"),
        )


class MySQLIdempotencyStore:
    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings

    def reserve(self, key: str) -> None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Idempotency database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO orchestration_idempotency (idempotency_key) VALUES (%s)",
                (key,),
            )
            connection.commit()
        except IntegrityError as exc:
            connection.rollback()
            raise DuplicateActionError(
                f"Duplicate action blocked for idempotency key '{key}'"
            ) from exc
        finally:
            cursor.close()
            connection.close()
