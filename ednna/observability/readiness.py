from __future__ import annotations

import os
from dataclasses import dataclass

from ednna.governance.action_execution import action_execution_mode_valid


@dataclass(frozen=True)
class ReadinessCheck:
    component: str
    ready: bool
    reason: str | None = None


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    checks: tuple[ReadinessCheck, ...]


def _enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def _missing(*names: str) -> tuple[str, ...]:
    return tuple(name for name in names if not os.getenv(name, "").strip())


class ReadinessChecker:
    """Validate configuration dependencies without exposing secret values."""

    def check(self) -> ReadinessReport:
        checks = [
            self._base_app(),
            self._database(),
            self._oidc(),
            self._action_execution_mode(),
            self._eddy(),
            self._servicebus(),
            self._specialist_catalog(),
            self._specialist_health_worker(),
        ]
        active = tuple(check for check in checks if check is not None)
        return ReadinessReport(
            ready=all(check.ready for check in active),
            checks=active,
        )

    @staticmethod
    def _base_app() -> ReadinessCheck:
        missing = _missing("SECRET_KEY", "ADMIN_PASSWORD")
        return ReadinessCheck(
            component="application",
            ready=not missing,
            reason=f"missing:{','.join(missing)}" if missing else None,
        )

    @staticmethod
    def _database() -> ReadinessCheck | None:
        db_required = any(
            _enabled(flag)
            for flag in (
                "APPROVAL_API_ENABLED",
                "ACTION_API_ENABLED",
                "EVENT_INGRESS_API_ENABLED",
                "SERVICEBUS_OUTBOX_ENABLED",
                "SERVICEBUS_CONSUMER_ENABLED",
                "SPECIALIST_AVAILABILITY_DURABLE",
                "SPECIALIST_HEALTH_WORKER_ENABLED",
            )
        )
        if not db_required:
            return None

        missing = _missing("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")
        return ReadinessCheck(
            component="database",
            ready=not missing,
            reason=f"missing:{','.join(missing)}" if missing else None,
        )

    @staticmethod
    def _oidc() -> ReadinessCheck | None:
        oidc_required = any(
            _enabled(flag)
            for flag in (
                "APPROVAL_API_ENABLED",
                "ACTION_API_ENABLED",
                "MULTIAGENT_QUERY_API_ENABLED",
                "EVENT_INGRESS_API_ENABLED",
            )
        )
        if not oidc_required:
            return None

        missing = _missing("OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL")
        return ReadinessCheck(
            component="oidc",
            ready=not missing,
            reason=f"missing:{','.join(missing)}" if missing else None,
        )

    @staticmethod
    def _action_execution_mode() -> ReadinessCheck | None:
        if not _enabled("ACTION_API_ENABLED"):
            return None

        valid = action_execution_mode_valid()
        return ReadinessCheck(
            component="action_execution_mode",
            ready=valid,
            reason=None if valid else "invalid_action_execution_mode",
        )

    @staticmethod
    def _eddy() -> ReadinessCheck | None:
        if not (_enabled("EDDY_ENABLED") or _enabled("ACTION_API_ENABLED")):
            return None

        missing = _missing("EDDY_BASE_URL", "EDDY_API_TOKEN")
        return ReadinessCheck(
            component="eddy",
            ready=not missing,
            reason=f"missing:{','.join(missing)}" if missing else None,
        )

    @staticmethod
    def _servicebus() -> ReadinessCheck | None:
        if not (
            _enabled("SERVICEBUS_OUTBOX_ENABLED")
            or _enabled("SERVICEBUS_CONSUMER_ENABLED")
        ):
            return None

        required = ["SERVICEBUS_NAMESPACE", "SERVICEBUS_TOPIC"]
        if _enabled("SERVICEBUS_CONSUMER_ENABLED"):
            required.append("SERVICEBUS_SUBSCRIPTION")

        missing = _missing(*required)
        return ReadinessCheck(
            component="servicebus",
            ready=not missing,
            reason=f"missing:{','.join(missing)}" if missing else None,
        )

    @staticmethod
    def _specialist_health_worker() -> ReadinessCheck | None:
        if not _enabled("SPECIALIST_HEALTH_WORKER_ENABLED"):
            return None

        durable = _enabled("SPECIALIST_AVAILABILITY_DURABLE")
        return ReadinessCheck(
            component="specialist_health_worker",
            ready=durable,
            reason=None if durable else "durable_availability_required",
        )

    @staticmethod
    def _specialist_catalog() -> ReadinessCheck | None:
        path = os.getenv("SPECIALIST_MANIFEST_PATH", "").strip()
        if not path:
            return None

        return ReadinessCheck(
            component="specialist_catalog",
            ready=os.path.isfile(path),
            reason=None if os.path.isfile(path) else "manifest_not_found",
        )
