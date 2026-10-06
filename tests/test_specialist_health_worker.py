from ednna.workers.specialist_health_worker import SpecialistHealthWorker


class FakeRefresher:
    def __init__(self):
        self.calls = 0
        self.worker = None

    def refresh(self):
        self.calls += 1
        if self.worker is not None:
            self.worker.request_stop()


def test_health_worker_refreshes_and_can_shutdown():
    refresher = FakeRefresher()
    worker = SpecialistHealthWorker(refresher, poll_interval_seconds=0)
    refresher.worker = worker

    assert worker.run() == 0
    assert refresher.calls == 1
