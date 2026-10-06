from __future__ import annotations

from ednna.infrastructure.database import connect_mysql
from ednna.settings import DatabaseSettings

from .availability import (
    SpecialistAvailability,
    SpecialistAvailabilityState,
)


class MySQLSpecialistAvailabilityStore:
    def __init__(self, settings: DatabaseSettings) -> None:
        self._settings = settings

    def set(
        self,
        specialist_id: str,
        status: SpecialistAvailability,
        reason_code: str | None = None,
    ) -> None:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Specialist availability database is unavailable")
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO orchestration_specialist_availability (
                    specialist_id, status, reason_code
                ) VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    reason_code = VALUES(reason_code)
                """,
                (
                    specialist_id,
                    status.value,
                    reason_code,
                ),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    def get(self, specialist_id: str) -> SpecialistAvailabilityState:
        connection = connect_mysql(self._settings)
        if connection is None:
            raise RuntimeError("Specialist availability database is unavailable")
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT specialist_id, status, reason_code
                FROM orchestration_specialist_availability
                WHERE specialist_id = %s
                """,
                (specialist_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return SpecialistAvailabilityState(
                    specialist_id=specialist_id,
                    status=SpecialistAvailability.UNKNOWN,
                )

            return SpecialistAvailabilityState(
                specialist_id=row["specialist_id"],
                status=SpecialistAvailability(row["status"]),
                reason_code=row["reason_code"],
            )
        finally:
            cursor.close()
            connection.close()

    def is_routable(self, specialist_id: str) -> bool:
        return self.get(specialist_id).status in {
            SpecialistAvailability.READY,
            SpecialistAvailability.DEGRADED,
        }

    def quarantine(self, specialist_id: str, reason_code: str) -> None:
        self.set(
            specialist_id,
            SpecialistAvailability.QUARANTINED,
            reason_code=reason_code,
        )
