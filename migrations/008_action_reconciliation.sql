ALTER TABLE orchestration_action_executions
    ADD COLUMN reconciled_at DATETIME(6) NULL AFTER error_type,
    ADD COLUMN reconciled_by VARCHAR(128) NULL AFTER reconciled_at,
    ADD COLUMN reconciliation_note TEXT NULL AFTER reconciled_by,
    ADD COLUMN reconciliation_reference VARCHAR(512) NULL AFTER reconciliation_note;

INSERT IGNORE INTO orchestration_schema_migrations (version, filename)
VALUES ('008', '008_action_reconciliation.sql');
