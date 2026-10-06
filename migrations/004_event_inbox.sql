CREATE TABLE IF NOT EXISTS orchestration_event_inbox (
    event_id VARCHAR(64) PRIMARY KEY,
    event_type VARCHAR(128) NOT NULL,
    source VARCHAR(128) NOT NULL,
    trace_id VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(128) NOT NULL,
    subject VARCHAR(255) NULL,
    occurred_at DATETIME(6) NOT NULL,
    received_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    data_json JSON NOT NULL,
    INDEX idx_event_inbox_trace (trace_id),
    INDEX idx_event_inbox_tenant_type (tenant_id, event_type),
    INDEX idx_event_inbox_received (received_at)
);

INSERT IGNORE INTO orchestration_schema_migrations (version, filename)
VALUES ('004', '004_event_inbox.sql');
