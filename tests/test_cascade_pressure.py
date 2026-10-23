import unittest

from control.cascade_pressure import CascadePressureController


class CascadePressureControllerTests(unittest.TestCase):

    def test_nominal_pressure_returns_nominal_fuel_command(self):
        controller = CascadePressureController()

        command = controller.update(
            measured_pressure_pu=1.0,
            dt=0.1,
        )

        self.assertAlmostEqual(command, 1.0)

    def test_low_pressure_increases_fuel_command(self):
        controller = CascadePressureController()

        command = controller.update(
            measured_pressure_pu=0.95,
            dt=0.1,
        )

        self.assertGreater(command, 1.0)

    def test_high_pressure_reduces_fuel_command(self):
        controller = CascadePressureController()

        command = controller.update(
            measured_pressure_pu=1.05,
            dt=0.1,
        )

        self.assertLess(command, 1.0)

    def test_fuel_command_stays_within_limits(self):
        controller = CascadePressureController()

        low_pressure_command = controller.update(
            measured_pressure_pu=-100.0,
            dt=0.1,
        )

        controller.reset()

        high_pressure_command = controller.update(
            measured_pressure_pu=100.0,
            dt=0.1,
        )

        self.assertGreaterEqual(low_pressure_command, 0.0)
        self.assertLessEqual(low_pressure_command, 1.5)
        self.assertGreaterEqual(high_pressure_command, 0.0)
        self.assertLessEqual(high_pressure_command, 1.5)

    def test_reset_clears_controller_history(self):
        controller = CascadePressureController()

        controller.update(measured_pressure_pu=0.9, dt=0.1)
        controller.reset()

        command = controller.update(
            measured_pressure_pu=1.0,
            dt=0.1,
        )

        self.assertAlmostEqual(command, 1.0)

    def test_nonpositive_timestep_is_rejected(self):
        controller = CascadePressureController()

        for dt in (0.0, -0.1):
            with self.subTest(dt=dt):
                with self.assertRaises(ValueError):
                    controller.update(
                        measured_pressure_pu=1.0,
                        dt=dt,
                    )


if __name__ == "__main__":
    unittest.main()
