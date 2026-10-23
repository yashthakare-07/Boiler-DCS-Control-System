import unittest

from model.boiler import BoilerModel
from safety.interlocks import SafetyInterlock
from plc_interface.adapter import build_boiler_registers


class BoilerRegisterAdapterTests(unittest.TestCase):

    def test_normal_state_produces_thirteen_registers(self):
        boiler = BoilerModel()
        safety = SafetyInterlock()
        status = safety.evaluate(
            level_pct=boiler.state.drum_level_pct,
            pressure_pu=boiler.state.pressure_pu,
        )

        registers = build_boiler_registers(
            state=boiler.state,
            feedwater_command_pu=1.0,
            requested_fuel_command_pu=1.1,
            safety_status=status,
        )

        self.assertEqual(len(registers), 13)
        self.assertEqual(registers[0], 5000)
        self.assertEqual(registers[1], 10000)
        self.assertEqual(registers[7], 1100)
        self.assertEqual(registers[8], 0)
        self.assertEqual(registers[9], 1)
        self.assertEqual(registers[10], 0)
        self.assertEqual(registers[12], 1)

    def test_safety_trip_overrides_requested_fuel_command(self):
        boiler = BoilerModel()
        safety = SafetyInterlock()

        status = safety.evaluate(
            level_pct=boiler.state.drum_level_pct,
            pressure_pu=boiler.state.pressure_pu,
            sensors_valid=False,
        )

        registers = build_boiler_registers(
            state=boiler.state,
            feedwater_command_pu=1.0,
            requested_fuel_command_pu=1.2,
            safety_status=status,
        )

        self.assertEqual(registers[7], 0)
        self.assertEqual(registers[8], 1)
        self.assertEqual(registers[9], 0)
        self.assertEqual(registers[10], 1)
        self.assertEqual(registers[11], 1 << 6)

    def test_stopped_simulation_status(self):
        boiler = BoilerModel()
        safety = SafetyInterlock()
        status = safety.evaluate(
            level_pct=boiler.state.drum_level_pct,
            pressure_pu=boiler.state.pressure_pu,
        )

        registers = build_boiler_registers(
            state=boiler.state,
            feedwater_command_pu=1.0,
            requested_fuel_command_pu=1.0,
            safety_status=status,
            simulation_running=False,
        )

        self.assertEqual(registers[12], 0)


if __name__ == "__main__":
    unittest.main()
