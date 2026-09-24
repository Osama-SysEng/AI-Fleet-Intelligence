from .contracts import TelemetryPoint, coarse_location
from .risk import assess

class SimulationFleetStore:
    def __init__(self): self._seen, self._events, self._audit = set(), [], []
    def ingest(self, raw: dict) -> dict:
        point = __import__("backend.app.fleet.contracts", fromlist=["parse_telemetry"]).parse_telemetry(raw)
        key = f"{point.vehicle_id}:{point.sequence}"
        if key in self._seen: return {"accepted": True, "duplicate": True, "event": None}
        self._seen.add(key); recommendation = assess(point)
        event = {"id": f"evt_{len(self._events)+1}", "vehicle_id": point.vehicle_id, "occurred_at": point.occurred_at.isoformat(), "location": coarse_location(point), "readings": {"speed_kph": point.speed_kph, "fuel_percent": point.fuel_percent, "engine_temp_c": point.engine_temp_c}, "recommendation": recommendation.__dict__}
        self._events.append(event); self._audit.append({"type": "telemetry_accepted", "event_id": event["id"], "level": recommendation.level})
        return {"accepted": True, "duplicate": False, "event": event}
    def events(self): return list(reversed(self._events))
    def audit(self): return list(reversed(self._audit))
