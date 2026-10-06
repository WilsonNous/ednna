CREATE TABLE IF NOT EXISTS orchestration_action_executions (
    idempotency_key VARCHAR(255) PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    capability VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(128) NULL,
    requested_by VARCHAR(128) NULL,
    status VARCHAR(32) NOT NULL,
    started_at DATETIME(6) NOT NULL,
    completed_at DATETIME(6) NULL,
    specialist_id VARCHAR(128) NULL,
    response_status VARCHAR(64) NULL,
    evidence_count INT NOT NULL DEFAULT 0,
    error_type VARCHAR(128) NULL,
    INDEX idx_action_exec_trace (trace_id),
    INDEX idx_action_exec_status (status)
);

INSERT IGNORE INTO orchestration_schema_migrations (version, filename)
VALUES ('007', '007_action_execution_ledger.sql');
