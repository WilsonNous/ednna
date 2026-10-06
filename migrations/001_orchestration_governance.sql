CREATE TABLE IF NOT EXISTS orchestration_audit_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_timestamp DATETIME(6) NOT NULL,
    user_id VARCHAR(128) NULL,
    tenant_id VARCHAR(128) NULL,
    conversation_id VARCHAR(128) NULL,
    specialist_id VARCHAR(128) NULL,
    capability VARCHAR(255) NULL,
    status VARCHAR(64) NULL,
    confidence DECIMAL(8,6) NULL,
    requires_human BOOLEAN NULL,
    details_json JSON NOT NULL,
    INDEX idx_audit_trace (trace_id),
    INDEX idx_audit_timestamp (event_timestamp)
);

CREATE TABLE IF NOT EXISTS orchestration_approvals (
    approval_id VARCHAR(64) PRIMARY KEY,
    trace_id VARCHAR(64) NOT NULL,
    capability VARCHAR(255) NOT NULL,
    specialist_id VARCHAR(128) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(32) NOT NULL,
    requested_at DATETIME(6) NOT NULL,
    decided_at DATETIME(6) NULL,
    decided_by VARCHAR(128) NULL,
    decision_note TEXT NULL,
    INDEX idx_approval_trace (trace_id),
    INDEX idx_approval_status (status)
);

CREATE TABLE IF NOT EXISTS orchestration_idempotency (
    idempotency_key VARCHAR(255) PRIMARY KEY,
    reserved_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
);

INSERT IGNORE INTO orchestration_schema_migrations (version, filename)
VALUES ('001', '001_orchestration_governance.sql');
