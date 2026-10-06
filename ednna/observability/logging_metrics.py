from __future__ import annotations

import json
import logging


class LoggingMetricsRecorder:
    """Emit privacy-safe structured metric events through standard logging."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("ednna.metrics")

    def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: dict[str, str] | None = None,
    ) -> None:
        self._emit("counter", name, value, tags)

    def observe(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        self._emit("observation", name, value, tags)

    def gauge(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        self._emit("gauge", name, value, tags)

    def _emit(
        self,
        metric_type: str,
        name: str,
        value: float,
        tags: dict[str, str] | None,
    ) -> None:
        self._logger.info(
            json.dumps(
                {
                    "event": "metric",
                    "metric_type": metric_type,
                    "name": name,
                    "value": value,
                    "tags": tags or {},
                },
                sort_keys=True,
            )
        )
