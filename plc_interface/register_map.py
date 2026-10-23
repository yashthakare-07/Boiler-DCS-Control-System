"""Scaled 16-bit Modbus holding-register map for the boiler digital twin."""

from math import isfinite


REGISTER_MAP = {
    "drum_level_pct": {"address": 0, "scale": 100.0},
    "pressure_pu": {"address": 1, "scale": 10000.0},
    "steam_flow_pu": {"address": 2, "scale": 1000.0},
    "feedwater_flow_pu": {"address": 3, "scale": 1000.0},
    "fuel_flow_pu": {"address": 4, "scale": 1000.0},
    "heat_duty_pu": {"address": 5, "scale": 1000.0},
    "feedwater_command_pu": {"address": 6, "scale": 1000.0},
    "fuel_command_pu": {"address": 7, "scale": 1000.0},
    "trip_latched": {"address": 8, "scale": 1.0},
    "fuel_permissive": {"address": 9, "scale": 1.0},
    "alarm_active": {"address": 10, "scale": 1.0},
    "trip_cause_mask": {"address": 11, "scale": 1.0},
    "simulation_status": {"address": 12, "scale": 1.0},
}

REGISTER_COUNT = max(
    item["address"] for item in REGISTER_MAP.values()
) + 1

TRIP_CAUSE_BITS = {
    "LOW_LOW_DRUM_LEVEL": 0,
    "HIGH_HIGH_DRUM_LEVEL": 1,
    "LOW_LOW_PRESSURE": 2,
    "HIGH_HIGH_PRESSURE": 3,
    "LEVEL_SIGNAL_OUT_OF_RANGE": 4,
    "PRESSURE_SIGNAL_OUT_OF_RANGE": 5,
    "SENSOR_INVALID": 6,
    "COMMUNICATION_LOSS": 7,
}


def encode_value(name, value):
    """Convert one named value to an unsigned 16-bit register value."""
    if name not in REGISTER_MAP:
        raise KeyError(f"Unknown register name: {name}")

    if isinstance(value, bool):
        numeric_value = int(value)
    else:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Invalid value for {name}") from exc

    if not isfinite(numeric_value):
        raise ValueError(f"Non-finite value for {name}")

    scaled = round(numeric_value * REGISTER_MAP[name]["scale"])

    if not 0 <= scaled <= 65535:
        raise ValueError(
            f"Encoded value for {name} is outside unsigned 16-bit range: "
            f"{scaled}"
        )

    return int(scaled)


def decode_value(name, register_value):
    """Convert one unsigned 16-bit register value to engineering units."""
    if name not in REGISTER_MAP:
        raise KeyError(f"Unknown register name: {name}")

    if isinstance(register_value, bool) or not isinstance(register_value, int):
        raise ValueError("Register value must be an integer")

    if not 0 <= register_value <= 65535:
        raise ValueError("Register value must be between 0 and 65535")

    return register_value / REGISTER_MAP[name]["scale"]


def encode_trip_causes(causes):
    """Encode recognized trip causes into a 16-bit bitmask."""
    mask = 0
    for cause in causes:
        if cause not in TRIP_CAUSE_BITS:
            raise ValueError(f"Unknown trip cause: {cause}")
        mask |= 1 << TRIP_CAUSE_BITS[cause]
    return mask


def build_register_image(values):
    """Build a complete address-indexed holding-register image.

    Every defined register must be provided. Unknown names are rejected.
    """
    unknown = set(values) - set(REGISTER_MAP)
    missing = set(REGISTER_MAP) - set(values)

    if unknown:
        raise KeyError(f"Unknown register names: {sorted(unknown)}")
    if missing:
        raise KeyError(f"Missing register names: {sorted(missing)}")

    registers = [0] * REGISTER_COUNT

    for name, value in values.items():
        registers[REGISTER_MAP[name]["address"]] = encode_value(name, value)

    return registers
