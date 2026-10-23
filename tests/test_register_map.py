import unittest

from plc_interface.register_map import (
    REGISTER_MAP,
    REGISTER_COUNT,
    build_register_image,
    decode_value,
    encode_trip_causes,
    encode_value,
)


class RegisterMapTests(unittest.TestCase):

    def test_register_addresses_are_unique(self):
        addresses = [
            item["address"] for item in REGISTER_MAP.values()
        ]
        self.assertEqual(len(addresses), len(set(addresses)))

    def test_register_count_is_thirteen(self):
        self.assertEqual(REGISTER_COUNT, 13)

    def test_pressure_round_trip(self):
        encoded = encode_value("pressure_pu", 1.2345)
        self.assertEqual(encoded, 12345)
        self.assertAlmostEqual(
            decode_value("pressure_pu", encoded), 1.2345
        )

    def test_level_round_trip(self):
        encoded = encode_value("drum_level_pct", 50.25)
        self.assertEqual(encoded, 5025)
        self.assertAlmostEqual(
            decode_value("drum_level_pct", encoded), 50.25
        )

    def test_boolean_register(self):
        self.assertEqual(encode_value("trip_latched", True), 1)
        self.assertEqual(encode_value("trip_latched", False), 0)

    def test_invalid_numeric_values_are_rejected(self):
        for value in (float("nan"), float("inf"), -1.0):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    encode_value("pressure_pu", value)

    def test_unsigned_register_overflow_is_rejected(self):
        with self.assertRaises(ValueError):
            encode_value("drum_level_pct", 700.0)

    def test_unknown_register_is_rejected(self):
        with self.assertRaises(KeyError):
            encode_value("unknown_tag", 1.0)

    def test_trip_cause_bitmask(self):
        mask = encode_trip_causes(
            ("SENSOR_INVALID", "COMMUNICATION_LOSS")
        )
        self.assertEqual(mask, (1 << 6) | (1 << 7))

    def test_complete_register_image(self):
        values = {
            "drum_level_pct": 50.0,
            "pressure_pu": 1.0,
            "steam_flow_pu": 1.0,
            "feedwater_flow_pu": 1.0,
            "fuel_flow_pu": 1.0,
            "heat_duty_pu": 1.0,
            "feedwater_command_pu": 1.0,
            "fuel_command_pu": 0.0,
            "trip_latched": True,
            "fuel_permissive": False,
            "alarm_active": True,
            "trip_cause_mask": 64,
            "simulation_status": 1,
        }
        registers = build_register_image(values)

        self.assertEqual(len(registers), 13)
        self.assertEqual(registers[0], 5000)
        self.assertEqual(registers[1], 10000)
        self.assertEqual(registers[7], 0)
        self.assertEqual(registers[8], 1)
        self.assertEqual(registers[9], 0)
        self.assertEqual(registers[11], 64)

    def test_register_image_rejects_missing_values(self):
        with self.assertRaises(KeyError):
            build_register_image({})

    def test_register_image_rejects_unknown_values(self):
        with self.assertRaises(KeyError):
            build_register_image({"unexpected_tag": 1})


if __name__ == "__main__":
    unittest.main()
