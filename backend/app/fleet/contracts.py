from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class TelemetryPoint:
    vehicle_id: str
    sequence: int
    occurred_at: datetime
    latitude: float
    longitude: float
    speed_kph: float
    fuel_percent: float
    engine_temp_c: float

def parse_telemetry(raw: dict) -> TelemetryPoint:
    if not isinstance(raw, dict): raise ValueError("telemetry must be an object")
    vehicle_id = str(raw.get("vehicle_id", "")).strip()
    if not vehicle_id or len(vehicle_id) > 64: raise ValueError("vehicle_id is invalid")
    sequence = int(raw.get("sequence"))
    if sequence < 0: raise ValueError("sequence is invalid")
    occurred_at = datetime.fromisoformat(str(raw.get("occurred_at", "")).replace("Z", "+00:00"))
    if occurred_at.tzinfo is None: raise ValueError("occurred_at must include timezone")
    latitude, longitude = float(raw.get("latitude")), float(raw.get("longitude"))
    speed, fuel, temp = float(raw.get("speed_kph")), float(raw.get("fuel_percent")), float(raw.get("engine_temp_c"))
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180): raise ValueError("location out of range")
    if not (0 <= speed <= 260 and 0 <= fuel <= 100 and -40 <= temp <= 180): raise ValueError("reading out of simulation range")
    return TelemetryPoint(vehicle_id, sequence, occurred_at.astimezone(timezone.utc), latitude, longitude, speed, fuel, temp)

def coarse_location(point: TelemetryPoint) -> dict:
    return {"latitude": round(point.latitude, 2), "longitude": round(point.longitude, 2)}
