import unittest

from model.boiler import BoilerModel
from control import SingleElementController, ThreeElementController


class ClosedLoopTests(unittest.TestCase):

    def simulate(self, controller_type, duration_s=60.0, step_time_s=10.0):
        boiler = BoilerModel()
        controller = controller_type(setpoint_pct=50.0)
        dt = boiler.dt
        total_steps = round(duration_s / dt)
        disturbance_step = round(step_time_s / dt)
        samples = []

        for step_index in range(total_steps):
            state = boiler.state

            # Use the integer step index to avoid floating-point time errors.
            demand = 1.0 if step_index < disturbance_step else 1.2

            if controller_type is SingleElementController:
                command = controller.update(state.drum_level_pct, dt)
            else:
                command = controller.update(
                    state.drum_level_pct,
                    state.steam_flow_pu,
                    state.feedwater_flow_pu,
                    dt,
                )

            boiler.step(
                feedwater_command_pu=command,
                steam_demand_pu=demand,
                fuel_command_pu=1.0,
            )

            samples.append({
                "time_s": boiler.state.time_s,
                "level_pct": boiler.state.drum_level_pct,
                "inventory_pu": boiler.state.inventory_pu,
                "command_pu": command,
                "demand_pu": demand,
            })

        return samples, disturbance_step

    def test_both_controllers_keep_level_within_physical_bounds(self):
        for controller_type in (
            SingleElementController,
            ThreeElementController,
        ):
            with self.subTest(controller=controller_type.__name__):
                samples, _ = self.simulate(controller_type)
                for sample in samples:
                    self.assertGreaterEqual(sample["level_pct"], 0.0)
                    self.assertLessEqual(sample["level_pct"], 100.0)

    def test_both_controllers_keep_feedwater_command_bounded(self):
        for controller_type in (
            SingleElementController,
            ThreeElementController,
        ):
            with self.subTest(controller=controller_type.__name__):
                samples, _ = self.simulate(controller_type)
                for sample in samples:
                    self.assertGreaterEqual(sample["command_pu"], 0.0)
                    self.assertLessEqual(sample["command_pu"], 1.5)

    def test_steam_demand_increases_at_ten_seconds(self):
        for controller_type in (
            SingleElementController,
            ThreeElementController,
        ):
            with self.subTest(controller=controller_type.__name__):
                samples, disturbance_step = self.simulate(controller_type)
                before = samples[:disturbance_step]
                after = samples[disturbance_step:]

                self.assertTrue(before)
                self.assertTrue(after)
                self.assertTrue(
                    all(s["demand_pu"] == 1.0 for s in before)
                )
                self.assertTrue(
                    all(s["demand_pu"] == 1.2 for s in after)
                )

    def test_three_element_final_level_is_near_setpoint(self):
        samples, _ = self.simulate(ThreeElementController)
        final_level = samples[-1]["level_pct"]
        self.assertLessEqual(abs(final_level - 50.0), 1.0)


if __name__ == "__main__":
    unittest.main()
