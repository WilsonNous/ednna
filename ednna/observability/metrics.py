from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Protocol


@dataclass(frozen=True)
class MetricPoint:
    name: str
    value: float
    tags: tuple[tuple[str, str], ...] = ()


class MetricsRecorder(Protocol):
    def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: dict[str, str] | None = None,
    ) -> None:
        ...

    def observe(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        ...

    def gauge(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        ...


class InMemoryMetricsRecorder:
    """Small thread-safe metrics store used by tests and local diagnostics."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._observations: list[MetricPoint] = []
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}

    @staticmethod
    def _tags(tags: dict[str, str] | None) -> tuple[tuple[str, str], ...]:
        return tuple(sorted((tags or {}).items()))

    def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: dict[str, str] | None = None,
    ) -> None:
        key = (name, self._tags(tags))
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + value

    def observe(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        with self._lock:
            self._observations.append(
                MetricPoint(name=name, value=value, tags=self._tags(tags))
            )

    def gauge(
        self,
        name: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        key = (name, self._tags(tags))
        with self._lock:
            self._gauges[key] = value

    def counter_value(
        self,
        name: str,
        tags: dict[str, str] | None = None,
    ) -> float:
        return self._counters.get((name, self._tags(tags)), 0.0)

    def observations(self, name: str) -> tuple[MetricPoint, ...]:
        return tuple(point for point in self._observations if point.name == name)

    def gauge_value(
        self,
        name: str,
        tags: dict[str, str] | None = None,
    ) -> float | None:
        return self._gauges.get((name, self._tags(tags)))
