from __future__ import annotations

from ednna.infrastructure.database import connect_mysql
from ednna.settings import DatabaseSettings

from .approvals import ApprovalRequest, ApprovalStatus
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
                    approval_id, trace_id, capability, specialist_id, reason, status,
                    requested_at, decided_at, decided_by, decision_note
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    approval.reason,
                    approval.status.value,
                    approval.requested_at.replace(tzinfo=None),
                    approval.decided_at.replace(tzinfo=None) if approval.decided_at else None,
                    approval.decided_by,
                    approval.decision_note,
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
            if row is None:
                return None
            return ApprovalRequest(
                approval_id=row["approval_id"],
                trace_id=row["trace_id"],
                capability=row["capability"],
                specialist_id=row["specialist_id"],
                reason=row["reason"],
                status=ApprovalStatus(row["status"]),
                requested_at=row["requested_at"],
                decided_at=row["decided_at"],
                decided_by=row["decided_by"],
                decision_note=row["decision_note"],
            )
        finally:
            cursor.close()
            connection.close()


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
        except Exception as exc:
            connection.rollback()
            raise DuplicateActionError(
                f"Duplicate action blocked for idempotency key '{key}'"
            ) from exc
        finally:
            cursor.close()
            connection.close()
