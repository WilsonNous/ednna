ALTER TABLE orchestration_approvals
    ADD COLUMN tenant_id VARCHAR(128) NULL AFTER specialist_id,
    ADD COLUMN requested_by VARCHAR(128) NULL AFTER tenant_id,
    ADD INDEX idx_approval_tenant (tenant_id);
