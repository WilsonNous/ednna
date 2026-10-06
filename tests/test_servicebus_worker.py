from ednna.workers.servicebus_worker import ServiceBusWorker


def test_worker_can_be_stopped_before_running_cycle(monkeypatch):
    worker = ServiceBusWorker(poll_interval_seconds=0)
    worker.request_stop()

    assert worker.run() == 0


def test_worker_records_nonzero_cycle_but_can_shutdown(monkeypatch):
    worker = ServiceBusWorker(poll_interval_seconds=0)
    calls = {"count": 0}

    def fake_cycle():
        calls["count"] += 1
        worker.request_stop()
        return 1

    monkeypatch.setattr(
        "ednna.workers.servicebus_worker.consume_once",
        fake_cycle,
    )

    assert worker.run() == 1
    assert calls["count"] == 1
