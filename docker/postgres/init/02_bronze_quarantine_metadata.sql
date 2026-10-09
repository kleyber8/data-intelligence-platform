-- ============================================================
-- Fase 2 — Tablas de Bronze, Cuarentena y Metadatos
-- Ejecutado por la imagen de Postgres al crear el contenedor.
-- También aplicable manualmente: psql -f 02_...
-- ============================================================

-- ---------- metadata.ingestion_runs ----------
CREATE TABLE IF NOT EXISTS metadata.ingestion_runs (
    ingestion_run_id    UUID PRIMARY KEY,
    source_system       VARCHAR(100) NOT NULL,
    source_url          TEXT,
    source_file         VARCHAR(500),
    download_timestamp  TIMESTAMPTZ NOT NULL,
    file_size_bytes     BIGINT,
    checksum_sha256     VARCHAR(64),
    data_period_start   TIMESTAMPTZ,
    data_period_end     TIMESTAMPTZ,
    rows_ingested       INTEGER DEFAULT 0,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_status ON metadata.ingestion_runs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_download_ts ON metadata.ingestion_runs(download_timestamp DESC);

-- ---------- bronze.bronze_ais_position ----------
CREATE TABLE IF NOT EXISTS bronze.bronze_ais_position (
    record_id           BIGSERIAL PRIMARY KEY,
    ingestion_row_id    UUID NOT NULL,
    mmsi                VARCHAR(20),
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    speed_over_ground   DOUBLE PRECISION,
    course_over_ground  DOUBLE PRECISION,
    heading             INTEGER,
    position_ts         TIMESTAMPTZ,
    vessel_name         VARCHAR(255),
    vessel_type         VARCHAR(100),
    nav_status          VARCHAR(100),
    ingestion_run_id    UUID NOT NULL,
    source_file         VARCHAR(500),
    quality_status      VARCHAR(20) NOT NULL DEFAULT 'pending',
    quality_checked_at  TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_bronze_ais_position_run ON bronze.bronze_ais_position(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_bronze_ais_position_mmsi ON bronze.bronze_ais_position(mmsi);
CREATE INDEX IF NOT EXISTS idx_bronze_ais_position_ts ON bronze.bronze_ais_position(position_ts DESC);
CREATE INDEX IF NOT EXISTS idx_bronze_ais_position_status ON bronze.bronze_ais_position(quality_status);

-- ---------- quarantine.quarantine_records ----------
CREATE TABLE IF NOT EXISTS quarantine.quarantine_records (
    record_id            BIGSERIAL PRIMARY KEY,
    source_record_id     VARCHAR(100),
    failure_reason       TEXT NOT NULL,
    quality_rule         VARCHAR(100) NOT NULL,
    ingestion_run_id     UUID NOT NULL,
    source_table         VARCHAR(200),
    original_payload     JSONB NOT NULL,
    quarantine_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_quarantine_run ON quarantine.quarantine_records(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_quarantine_rule ON quarantine.quarantine_records(quality_rule);
