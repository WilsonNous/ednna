ALTER TABLE orchestration_approvals
    ADD COLUMN action_idempotency_key VARCHAR(255) NULL AFTER decision_note,
    ADD COLUMN action_bound_at DATETIME(6) NULL AFTER action_idempotency_key,
    ADD UNIQUE INDEX ux_approval_action_key (action_idempotency_key);

INSERT IGNORE INTO orchestration_schema_migrations (version, filename)
VALUES ('006', '006_approval_action_binding.sql');
