import math
import unittest

from model.boiler import BoilerModel
from control import SingleElementController, ThreeElementController


class DisturbanceMetricTests(unittest.TestCase):
    DURATION_S = 60.0
    DISTURBANCE_STEP = 100
    SETPOINT = 50.0
    TOLERANCE_PCT = 1.0

    def simulate(self, controller_type):
        boiler = BoilerModel()
        controller = controller_type(setpoint_pct=self.SETPOINT)
        dt = boiler.dt
        total_steps = round(self.DURATION_S / dt)
        rows = []

        for step_index in range(total_steps):
            state = boiler.state
            demand = 1.0 if step_index < self.DISTURBANCE_STEP else 1.2

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

            s = boiler.state
            rows.append({
                "time_s": s.time_s,
                "level_pct": s.drum_level_pct,
                "error_pct": self.SETPOINT - s.drum_level_pct,
                "command_pu": command,
                "demand_pu": demand,
            })

        post = rows[self.DISTURBANCE_STEP:]
        errors = [r["error_pct"] for r in post]

        settling_time = None
        for i, row in enumerate(post):
            remaining_errors = [
                abs(r["error_pct"]) for r in post[i:]
            ]
            if all(error <= self.TOLERANCE_PCT for error in remaining_errors):
                settling_time = row["time_s"] - 10.0
                break

        return {
            "iae_pct_s": sum(abs(e) for e in errors) * dt,
            "max_abs_error_pct": max(abs(e) for e in errors),
            "final_level_error_pct": errors[-1],
            "max_command_pu": max(r["command_pu"] for r in post),
            "min_command_pu": min(r["command_pu"] for r in post),
            "settling_time_s": settling_time,
        }

    def test_all_metrics_are_finite_except_unsettled_time(self):
        for controller_type in (
            SingleElementController,
            ThreeElementController,
        ):
            with self.subTest(controller=controller_type.__name__):
                result = self.simulate(controller_type)
                for key, value in result.items():
                    if key == "settling_time_s" and value is None:
                        continue
                    self.assertTrue(
                        math.isfinite(value),
                        f"{key} is not finite: {value}",
                    )

    def test_commands_remain_within_limits_after_disturbance(self):
        for controller_type in (
            SingleElementController,
            ThreeElementController,
        ):
            with self.subTest(controller=controller_type.__name__):
                result = self.simulate(controller_type)
                self.assertGreaterEqual(result["min_command_pu"], 0.0)
                self.assertLessEqual(result["max_command_pu"], 1.5)

    def test_three_element_final_level_error_is_within_one_percent(self):
        result = self.simulate(ThreeElementController)
        self.assertLessEqual(
            abs(result["final_level_error_pct"]),
            self.TOLERANCE_PCT,
        )

    def test_print_comparison_metrics(self):
        for controller_type in (
            SingleElementController,
            ThreeElementController,
        ):
            result = self.simulate(controller_type)
            print(f"\n{controller_type.__name__}")
            for key, value in result.items():
                print(f"  {key}: {value}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
