CREATE TABLE IF NOT EXISTS orchestration_event_outbox (
    event_id VARCHAR(64) PRIMARY KEY,
    event_type VARCHAR(128) NOT NULL,
    source VARCHAR(128) NOT NULL,
    trace_id VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(128) NULL,
    subject VARCHAR(255) NULL,
    occurred_at DATETIME(6) NOT NULL,
    data_json JSON NOT NULL,
    delivery_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    attempts INT NOT NULL DEFAULT 0,
    available_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    delivered_at DATETIME(6) NULL,
    last_error_type VARCHAR(128) NULL,
    INDEX idx_outbox_status_available (delivery_status, available_at),
    INDEX idx_outbox_trace (trace_id)
);
