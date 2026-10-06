import json
import logging

from ednna.observability.logging_metrics import LoggingMetricsRecorder


class CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def test_logging_metrics_emits_structured_json_without_extra_payload():
    logger = logging.getLogger("test.ednna.metrics")
    logger.setLevel(logging.INFO)
    handler = CaptureHandler()
    logger.addHandler(handler)

    recorder = LoggingMetricsRecorder(logger)
    recorder.increment(
        "ednna.events.processed",
        3,
        tags={"consumer": "servicebus"},
    )

    payload = json.loads(handler.messages[0])
    assert payload == {
        "event": "metric",
        "metric_type": "counter",
        "name": "ednna.events.processed",
        "value": 3,
        "tags": {"consumer": "servicebus"},
    }
