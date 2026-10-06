from __future__ import annotations

import os
import signal
import time
from dataclasses import dataclass

from ednna.events.consume_servicebus import main as consume_once


@dataclass
class WorkerState:
    stopping: bool = False


class ServiceBusWorker:
    def __init__(self, poll_interval_seconds: float = 2.0) -> None:
        self._poll_interval_seconds = poll_interval_seconds
        self._state = WorkerState()

    def request_stop(self, *_args) -> None:
        self._state.stopping = True

    def run(self) -> int:
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)

        exit_code = 0
        while not self._state.stopping:
            cycle_code = consume_once()
            if cycle_code != 0:
                exit_code = cycle_code

            if self._state.stopping:
                break

            time.sleep(self._poll_interval_seconds)

        return exit_code


def main() -> int:
    poll_interval = float(os.getenv("SERVICEBUS_WORKER_POLL_SECONDS", "2"))
    return ServiceBusWorker(poll_interval_seconds=poll_interval).run()


if __name__ == "__main__":
    raise SystemExit(main())
