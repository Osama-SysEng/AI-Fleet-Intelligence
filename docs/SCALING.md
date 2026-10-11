# SCALING — AI Fleet Intelligence (Simulation)

- Bottleneck: in-memory `SimulationFleetStore` (bounded by `MAX_STORE_EVENTS`, default 10000, hard cap 100000) + single-process idempotency.
- Tuning: `RATE_LIMIT_PER_MINUTE` (default 120, sliding window per IP+path, `/health` exempt); `MAX_STORE_EVENTS`; list endpoints `/events`/`/audit` capped `limit=50` default, `500` max.
- Known limits: single-process only — `docker/backend.Dockerfile` pins `--workers 1` because `vehicle_id:sequence` dedup lives in process memory; scaling beyond 1 worker or 1 replica needs a shared store (Redis/Postgres) and breaks idempotency; no DB pool (no database); rate limiter is per-process memory.
