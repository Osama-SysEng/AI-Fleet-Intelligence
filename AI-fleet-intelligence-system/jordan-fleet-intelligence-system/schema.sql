CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE TABLE vehicles (id TEXT PRIMARY KEY, plate TEXT UNIQUE NOT NULL, type TEXT NOT NULL, name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE drivers (id TEXT PRIMARY KEY, name TEXT NOT NULL, license TEXT, phone TEXT, vehicle_id TEXT REFERENCES vehicles(id), created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE telemetry (id BIGSERIAL, vehicle_id TEXT REFERENCES vehicles(id), driver_id TEXT REFERENCES drivers(id), lat DOUBLE PRECISION, lng DOUBLE PRECISION, speed DOUBLE PRECISION, fuel_level DOUBLE PRECISION, fuel_consumption DOUBLE PRECISION, engine_status TEXT, timestamp TIMESTAMPTZ NOT NULL);
SELECT create_hypertable('telemetry','timestamp', if_not_exists=>TRUE);
CREATE TABLE violations (id BIGSERIAL PRIMARY KEY, vehicle_id TEXT, driver_id TEXT, type TEXT, value DOUBLE PRECISION, threshold DOUBLE PRECISION, lat DOUBLE PRECISION, lng DOUBLE PRECISION, timestamp TIMESTAMPTZ, alert_sent BOOLEAN DEFAULT FALSE, resolved BOOLEAN DEFAULT FALSE);
CREATE INDEX telemetry_vehicle_time ON telemetry(vehicle_id,timestamp DESC);
CREATE INDEX violations_time ON violations(timestamp DESC);
