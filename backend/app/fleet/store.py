import os
from .contracts import TelemetryPoint, coarse_location, parse_telemetry
from .risk import assess


def _max_events() -> int:
    try:
        return max(100, min(int(os.getenv("MAX_STORE_EVENTS", "10000")), 100000))
    except ValueError:
        return 10000


class SimulationFleetStore:
    """In-memory simulation store. Single-process only: run uvicorn with
    --workers 1 so vehicle_id:sequence idempotency holds."""

    def __init__(self, max_events: int | None = None):
        self._seen: dict[str, None] = {}
        self._events: list[dict] = []
        self._audit: list[dict] = []
        self._max_events = max_events or _max_events()
        self._counter = 0

    def _evict_if_needed(self) -> None:
        while len(self._seen) > self._max_events:
            self._seen.pop(next(iter(self._seen)))
        del self._events[: max(0, len(self._events) - self._max_events)]
        del self._audit[: max(0, len(self._audit) - self._max_events)]

    def ingest(self, raw: dict) -> dict:
        point = parse_telemetry(raw)
        key = f"{point.vehicle_id}:{point.sequence}"
        if key in self._seen: return {"accepted": True, "duplicate": True, "event": None}
        self._seen[key] = None; recommendation = assess(point)
        self._counter += 1
        event = {"id": f"evt_{self._counter}", "vehicle_id": point.vehicle_id, "occurred_at": point.occurred_at.isoformat(), "location": coarse_location(point), "readings": {"speed_kph": point.speed_kph, "fuel_percent": point.fuel_percent, "engine_temp_c": point.engine_temp_c}, "recommendation": recommendation.__dict__}
        self._events.append(event); self._audit.append({"type": "telemetry_accepted", "event_id": event["id"], "level": recommendation.level})
        self._evict_if_needed()
        return {"accepted": True, "duplicate": False, "event": event}
    def events(self): return list(reversed(self._events))
    def audit(self): return list(reversed(self._audit))
