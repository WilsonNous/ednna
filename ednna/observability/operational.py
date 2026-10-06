from __future__ import annotations

from dataclasses import dataclass

from .metrics import MetricsRecorder


@dataclass(frozen=True)
class ConsumerCycleMetrics:
    processed: int
    failed: int
    dead_lettered: int


def record_consumer_cycle(
    metrics: MetricsRecorder,
    values: ConsumerCycleMetrics,
) -> None:
    metrics.increment("ednna.events.processed", values.processed)
    metrics.increment("ednna.events.failed", values.failed)
    metrics.increment("ednna.events.dead_lettered", values.dead_lettered)


def record_approval_created(
    metrics: MetricsRecorder,
    capability: str,
    specialist_id: str,
) -> None:
    metrics.increment(
        "ednna.approvals.created",
        tags={
            "capability": capability,
            "specialist": specialist_id,
        },
    )


def record_approval_decision(
    metrics: MetricsRecorder,
    capability: str,
    approved: bool,
) -> None:
    metrics.increment(
        "ednna.approvals.decided",
        tags={
            "capability": capability,
            "decision": "approved" if approved else "rejected",
        },
    )


def record_backlog(
    metrics: MetricsRecorder,
    pending_outbox: int,
    pending_approvals: int,
) -> None:
    metrics.gauge("ednna.events.outbox_pending", pending_outbox)
    metrics.gauge("ednna.approvals.pending", pending_approvals)
