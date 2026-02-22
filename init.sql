CREATE TABLE IF NOT EXISTS measurements (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sensor_id INTEGER NOT NULL,
    value NUMERIC(10, 2) NOT NULL,
    unit VARCHAR(10) DEFAULT 'C',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    prev_hash VARCHAR(64) NOT NULL,
    data_hash VARCHAR(64) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_measurements_recorded_at ON measurements (recorded_at);