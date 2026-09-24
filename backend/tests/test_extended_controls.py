import unittest

from backend.app.models.vehicle import TelemetryIn, Vehicle
from backend.app.services.telegram_alerts import TelegramAlertService
from backend.app.services.violation_engine import evaluate_telemetry


class ExtendedControlsTests(unittest.TestCase):
    def test_vehicle_rejects_extra_fields(self):
        with self.assertRaises(ValueError):
            Vehicle(vehicle_id="v1", fleet_id="f1", plate_number="12", vehicle_type="van", unexpected="x")

    def test_violation_engine_has_three_explainable_types(self):
        violations = evaluate_telemetry(speed_kph=140, fuel_percent=10, engine_temp_c=130)
        self.assertEqual({v.violation_type for v in violations}, {"speed_breach", "fuel_waste", "maintenance_temperature"})
        self.assertTrue(all(v.requires_review for v in violations))

    def test_telegram_is_blocked_by_default(self):
        service = TelegramAlertService(simulation_only=True)
        draft = service.draft("inc-1", "Review required")
        result = service.send(draft, human_approved=True)
        self.assertEqual(result.status, "blocked_pending_approval")
        self.assertEqual(result.external_dispatch, "not-attempted")

    def test_telemetry_is_bounded(self):
        with self.assertRaises(ValueError):
            TelemetryIn(vehicle_id="v1", sequence=1, occurred_at="2026-08-31T00:00:00Z", latitude=0, longitude=0, speed_kph=999, fuel_percent=50, engine_temp_c=80)


if __name__ == "__main__":
    unittest.main()
