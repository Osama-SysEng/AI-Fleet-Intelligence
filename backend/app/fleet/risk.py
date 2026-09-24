from dataclasses import dataclass
from .contracts import TelemetryPoint

@dataclass(frozen=True)
class FleetRecommendation:
    level: str
    signals: tuple[str, ...]
    recommendation: str
    external_dispatch: str = "not-attempted"
    vehicle_command: str = "prohibited-by-policy"

def assess(point: TelemetryPoint) -> FleetRecommendation:
    signals = []
    if point.speed_kph >= 120: signals.append("speed_review")
    if point.fuel_percent <= 12: signals.append("fuel_review")
    if point.engine_temp_c >= 105: signals.append("maintenance_review")
    level = "critical" if point.engine_temp_c >= 125 else "watch" if signals else "normal"
    text = "اطلب مراجعة مشرف الأسطول قبل أي تواصل أو إجراء." if signals else "استمر في المراقبة ضمن بيئة المحاكاة."
    return FleetRecommendation(level, tuple(signals), text)
