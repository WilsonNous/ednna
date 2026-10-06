CREATE TABLE IF NOT EXISTS orchestration_specialist_availability (
    specialist_id VARCHAR(128) PRIMARY KEY,
    status VARCHAR(32) NOT NULL,
    reason_code VARCHAR(128) NULL,
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_specialist_availability_status (status)
);

INSERT IGNORE INTO orchestration_schema_migrations (version, filename)
VALUES ('005', '005_specialist_availability.sql');
