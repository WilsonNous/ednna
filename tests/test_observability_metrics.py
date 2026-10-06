from ednna.observability.metrics import InMemoryMetricsRecorder
from ednna.observability.operational import (
    ConsumerCycleMetrics,
    record_backlog,
    record_consumer_cycle,
)


def test_metrics_recorder_tracks_counters_observations_and_gauges():
    metrics = InMemoryMetricsRecorder()

    metrics.increment("requests", tags={"specialist": "eddy"})
    metrics.increment("requests", tags={"specialist": "eddy"})
    metrics.observe("latency_ms", 12.5, tags={"specialist": "eddy"})
    metrics.gauge("pending", 4)

    assert metrics.counter_value("requests", {"specialist": "eddy"}) == 2
    assert metrics.observations("latency_ms")[0].value == 12.5
    assert metrics.gauge_value("pending") == 4


def test_operational_helpers_record_consumer_and_backlog_metrics():
    metrics = InMemoryMetricsRecorder()

    record_consumer_cycle(
        metrics,
        ConsumerCycleMetrics(processed=10, failed=2, dead_lettered=1),
    )
    record_backlog(metrics, pending_outbox=7, pending_approvals=3)

    assert metrics.counter_value("ednna.events.processed") == 10
    assert metrics.counter_value("ednna.events.failed") == 2
    assert metrics.counter_value("ednna.events.dead_lettered") == 1
    assert metrics.gauge_value("ednna.events.outbox_pending") == 7
    assert metrics.gauge_value("ednna.approvals.pending") == 3
