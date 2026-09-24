from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Violation:
    violation_type: str
    severity: str
    reason: str
    requires_review: bool = True


def evaluate_telemetry(*, speed_kph: float, fuel_percent: float, engine_temp_c: float, speed_limit_kph: float = 100.0) -> list[Violation]:
    """Return explainable signals only; never dispatches or controls a vehicle."""
    if not 0 <= speed_kph <= 260 or not 0 <= fuel_percent <= 100 or not -40 <= engine_temp_c <= 180:
        raise ValueError("telemetry outside policy bounds")
    if not 1 <= speed_limit_kph <= 200:
        raise ValueError("speed limit outside policy bounds")
    results: list[Violation] = []
    if speed_kph > speed_limit_kph:
        severity = "high" if speed_kph - speed_limit_kph >= 30 else "medium"
        results.append(Violation("speed_breach", severity, "speed exceeded the configured review threshold"))
    if fuel_percent <= 12:
        results.append(Violation("fuel_waste", "medium", "fuel level is below the configured review threshold"))
    if engine_temp_c >= 105:
        severity = "critical" if engine_temp_c >= 125 else "high"
        results.append(Violation("maintenance_temperature", severity, "engine temperature requires maintenance review"))
    return results


def explain(violations: list[Violation]) -> dict[str, Any]:
    return {"count": len(violations), "violations": [v.__dict__ for v in violations], "external_dispatch": "not-attempted", "vehicle_command": "prohibited-by-policy"}
