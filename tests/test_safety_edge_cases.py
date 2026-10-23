import unittest

from safety.interlocks import SafetyConfig, SafetyInterlock


class SafetyEdgeCaseTests(unittest.TestCase):
    def test_nan_pressure_trips(self):
        status = SafetyInterlock().evaluate(50.0, float("nan"))
        self.assertTrue(status.trip_latched)
        self.assertIn("SENSOR_INVALID", status.trip_causes)
        self.assertEqual(status.fuel_command_pu, 0.0)

    def test_nan_level_trips(self):
        status = SafetyInterlock().evaluate(float("nan"), 1.0)
        self.assertTrue(status.trip_latched)
        self.assertIn("SENSOR_INVALID", status.trip_causes)

    def test_infinite_pressure_trips(self):
        status = SafetyInterlock().evaluate(50.0, float("inf"))
        self.assertTrue(status.trip_latched)
        self.assertIn("SENSOR_INVALID", status.trip_causes)

    def test_non_numeric_measurement_trips(self):
        status = SafetyInterlock().evaluate(50.0, "bad-signal")
        self.assertTrue(status.trip_latched)
        self.assertIn("SENSOR_INVALID", status.trip_causes)

    def test_non_finite_thresholds_are_rejected(self):
        config = SafetyConfig(high_high_pressure_pu=float("nan"))
        with self.assertRaises(ValueError):
            SafetyInterlock(config)


if __name__ == "__main__":
    unittest.main()
