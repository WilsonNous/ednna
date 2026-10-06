CREATE TABLE IF NOT EXISTS orchestration_schema_migrations (
    version VARCHAR(32) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    applied_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
);

INSERT IGNORE INTO orchestration_schema_migrations (version, filename)
VALUES ('000', '000_schema_migrations.sql');
