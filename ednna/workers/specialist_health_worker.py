from __future__ import annotations

import logging
import os
import signal
import time
from dataclasses import dataclass

from ednna.bootstrap import build_availability_store
from ednna.orchestration.registry import SpecialistRegistry
from ednna.specialists.availability_feature_flags import specialist_availability_durable
from ednna.specialists.availability_refresh import SpecialistAvailabilityRefresher
from ednna.specialists.catalog import (
    build_manifest_clients,
    load_catalog_from_env,
    register_catalog,
)
from ednna.specialists.eddy import EDDY_DESCRIPTOR
from ednna.specialists.feature_flags import eddy_enabled
from ednna.specialists.health_worker_feature_flags import specialist_health_worker_enabled


@dataclass
class HealthWorkerState:
    stopping: bool = False


def build_health_refresh():
    manifests = load_catalog_from_env()
    registry = SpecialistRegistry()
    registry.register(EDDY_DESCRIPTOR)
    register_catalog(registry, manifests)

    clients = build_manifest_clients(manifests)
    if eddy_enabled():
        from ednna.specialists.eddy_client import build_eddy_client

        clients["eddy"] = build_eddy_client()

    availability = build_availability_store()
    return SpecialistAvailabilityRefresher(
        registry,
        availability,
        clients,
    )


class SpecialistHealthWorker:
    def __init__(
        self,
        refresher: SpecialistAvailabilityRefresher,
        poll_interval_seconds: float = 30.0,
    ) -> None:
        self._refresher = refresher
        self._poll_interval_seconds = poll_interval_seconds
        self._state = HealthWorkerState()

    def request_stop(self, *_args) -> None:
        self._state.stopping = True

    def run(self) -> int:
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)

        logger = logging.getLogger("ednna.specialist_health")
        exit_code = 0

        while not self._state.stopping:
            try:
                self._refresher.refresh()
                exit_code = 0
            except Exception as exc:
                exit_code = 1
                logger.error(
                    "specialist health refresh failed: %s",
                    type(exc).__name__,
                )

            if self._state.stopping:
                break

            time.sleep(self._poll_interval_seconds)

        return exit_code


def main() -> int:
    if not specialist_health_worker_enabled():
        return 0

    if not specialist_availability_durable():
        print("SPECIALIST_AVAILABILITY_DURABLE must be enabled for health worker.")
        return 1

    poll_interval = float(os.getenv("SPECIALIST_HEALTH_POLL_SECONDS", "30"))
    return SpecialistHealthWorker(
        build_health_refresh(),
        poll_interval_seconds=poll_interval,
    ).run()


if __name__ == "__main__":
    raise SystemExit(main())
