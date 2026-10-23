import unittest

from safety.interlocks import SafetyConfig, SafetyInterlock


class SafetyInterlockTests(unittest.TestCase):
    def setUp(self):
        self.safety = SafetyInterlock()

    def test_normal_conditions_allow_fuel(self):
        status = self.safety.evaluate(50.0, 1.0)

        self.assertFalse(status.trip_latched)
        self.assertTrue(status.fuel_permissive)
        self.assertEqual(status.fuel_command_pu, 1.0)
        self.assertFalse(status.alarm_active)

    def test_low_low_level_trips_fuel(self):
        status = self.safety.evaluate(20.0, 1.0)

        self.assertTrue(status.trip_latched)
        self.assertFalse(status.fuel_permissive)
        self.assertEqual(status.fuel_command_pu, 0.0)
        self.assertIn("LOW_LOW_DRUM_LEVEL", status.trip_causes)

    def test_high_high_level_trips_fuel(self):
        status = self.safety.evaluate(80.0, 1.0)

        self.assertTrue(status.trip_latched)
        self.assertEqual(status.fuel_command_pu, 0.0)
        self.assertIn("HIGH_HIGH_DRUM_LEVEL", status.trip_causes)

    def test_low_pressure_trips_fuel(self):
        status = self.safety.evaluate(50.0, 0.5)

        self.assertTrue(status.trip_latched)
        self.assertIn("LOW_LOW_PRESSURE", status.trip_causes)

    def test_high_pressure_trips_fuel(self):
        status = self.safety.evaluate(50.0, 1.5)

        self.assertTrue(status.trip_latched)
        self.assertIn("HIGH_HIGH_PRESSURE", status.trip_causes)

    def test_invalid_sensor_trips_fuel(self):
        status = self.safety.evaluate(
            50.0, 1.0, sensors_valid=False
        )

        self.assertTrue(status.trip_latched)
        self.assertIn("SENSOR_INVALID", status.trip_causes)

    def test_communication_loss_trips_fuel(self):
        status = self.safety.evaluate(
            50.0, 1.0, communication_ok=False
        )

        self.assertTrue(status.trip_latched)
        self.assertIn("COMMUNICATION_LOSS", status.trip_causes)

    def test_trip_remains_latched_after_condition_clears(self):
        self.safety.evaluate(10.0, 1.0)
        status = self.safety.evaluate(50.0, 1.0)

        self.assertTrue(status.trip_latched)
        self.assertEqual(status.fuel_command_pu, 0.0)

    def test_reset_requires_clear_conditions_and_manual_action(self):
        self.safety.evaluate(10.0, 1.0)

        blocked = self.safety.evaluate(
            10.0, 1.0, manual_reset=True
        )
        self.assertTrue(blocked.trip_latched)
        self.assertFalse(blocked.reset_accepted)

        reset = self.safety.evaluate(
            50.0, 1.0, manual_reset=True
        )
        self.assertFalse(reset.trip_latched)
        self.assertTrue(reset.reset_accepted)
        self.assertTrue(reset.fuel_permissive)

    def test_out_of_range_level_trips(self):
        status = self.safety.evaluate(101.0, 1.0)

        self.assertTrue(status.trip_latched)
        self.assertIn(
            "LEVEL_SIGNAL_OUT_OF_RANGE", status.trip_causes
        )

    def test_invalid_threshold_configuration_is_rejected(self):
        config = SafetyConfig(
            low_low_level_pct=90.0,
            high_high_level_pct=20.0,
        )

        with self.assertRaises(ValueError):
            SafetyInterlock(config)


if __name__ == "__main__":
    unittest.main()
