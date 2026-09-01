CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id TEXT PRIMARY KEY,
    fleet_id TEXT NOT NULL,
    plate_number TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    driver_id TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (fleet_id, plate_number)
);

CREATE TABLE IF NOT EXISTS telemetry_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id TEXT NOT NULL REFERENCES vehicles(vehicle_id),
    sequence BIGINT NOT NULL CHECK (sequence >= 0),
    occurred_at TIMESTAMPTZ NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    speed_kph DOUBLE PRECISION NOT NULL CHECK (speed_kph BETWEEN 0 AND 260),
    fuel_percent DOUBLE PRECISION NOT NULL CHECK (fuel_percent BETWEEN 0 AND 100),
    engine_temp_c DOUBLE PRECISION NOT NULL CHECK (engine_temp_c BETWEEN -40 AND 180),
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (vehicle_id, sequence)
);

CREATE INDEX IF NOT EXISTS telemetry_vehicle_time_idx ON telemetry_events (vehicle_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS telemetry_time_idx ON telemetry_events (occurred_at DESC);

CREATE TABLE IF NOT EXISTS violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id TEXT NOT NULL REFERENCES vehicles(vehicle_id),
    telemetry_sequence BIGINT NOT NULL,
    violation_type TEXT NOT NULL CHECK (violation_type IN ('speed_breach','fuel_waste','maintenance_temperature')),
    severity TEXT NOT NULL CHECK (severity IN ('medium','high','critical')),
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending_review' CHECK (status IN ('pending_review','reviewed','dismissed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (vehicle_id, telemetry_sequence, violation_type)
);

CREATE INDEX IF NOT EXISTS violations_review_idx ON violations (status, created_at DESC);
