from ednna.observability.readiness import ReadinessChecker


def set_base(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "secret")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin")


def test_readiness_is_ready_with_only_base_app_config(monkeypatch):
    set_base(monkeypatch)

    report = ReadinessChecker().check()

    assert report.ready is True
    assert {check.component for check in report.checks} == {"application"}


def test_oidc_dependency_is_required_only_when_feature_is_enabled(monkeypatch):
    set_base(monkeypatch)
    monkeypatch.setenv("MULTIAGENT_QUERY_API_ENABLED", "true")
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
    monkeypatch.delenv("OIDC_JWKS_URL", raising=False)

    report = ReadinessChecker().check()

    oidc = next(check for check in report.checks if check.component == "oidc")
    assert oidc.ready is False
    assert "OIDC_ISSUER" in oidc.reason
    assert report.ready is False


def test_servicebus_consumer_requires_subscription(monkeypatch):
    set_base(monkeypatch)
    monkeypatch.setenv("SERVICEBUS_CONSUMER_ENABLED", "true")
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("DB_NAME", "ednna")
    monkeypatch.setenv("SERVICEBUS_NAMESPACE", "example.servicebus.windows.net")
    monkeypatch.setenv("SERVICEBUS_TOPIC", "events")
    monkeypatch.delenv("SERVICEBUS_SUBSCRIPTION", raising=False)

    report = ReadinessChecker().check()

    servicebus = next(check for check in report.checks if check.component == "servicebus")
    assert servicebus.ready is False
    assert servicebus.reason == "missing:SERVICEBUS_SUBSCRIPTION"


def test_specialist_health_worker_requires_durable_availability(monkeypatch):
    set_base(monkeypatch)
    monkeypatch.setenv("SPECIALIST_HEALTH_WORKER_ENABLED", "true")
    monkeypatch.setenv("SPECIALIST_AVAILABILITY_DURABLE", "false")
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("DB_NAME", "ednna")

    report = ReadinessChecker().check()

    worker = next(
        check
        for check in report.checks
        if check.component == "specialist_health_worker"
    )
    assert worker.ready is False
    assert worker.reason == "durable_availability_required"
    assert report.ready is False
