import unittest
from backend.app.fleet.store import SimulationFleetStore

def sample(sequence=1, speed=70, fuel=50, temp=80): return {"vehicle_id":"sim-fleet-01","sequence":sequence,"occurred_at":"2026-08-24T10:00:00Z","latitude":31.95,"longitude":35.91,"speed_kph":speed,"fuel_percent":fuel,"engine_temp_c":temp}
class FleetCoreTests(unittest.TestCase):
    def test_event_hides_precise_location_and_prevents_dispatch(self):
        event = SimulationFleetStore().ingest(sample(speed=130))["event"]
        self.assertEqual(event["location"], {"latitude":31.95,"longitude":35.91})
        self.assertEqual(event["recommendation"]["external_dispatch"], "not-attempted")
    def test_telemetry_is_idempotent(self):
        store=SimulationFleetStore(); store.ingest(sample()); self.assertTrue(store.ingest(sample())["duplicate"])
    def test_critical_maintenance_is_explainable(self):
        event=SimulationFleetStore().ingest(sample(temp=130))["event"]
        self.assertEqual(event["recommendation"]["level"], "critical")
        self.assertIn("maintenance_review", event["recommendation"]["signals"])
if __name__ == "__main__": unittest.main()
