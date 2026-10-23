"""Educational boiler safety interlocks; not a certified safety system."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class SafetyConfig:
    low_low_level_pct: float = 20.0
    high_high_level_pct: float = 80.0
    low_low_pressure_pu: float = 0.5
    high_high_pressure_pu: float = 1.5


@dataclass(frozen=True)
class SafetyStatus:
    trip_latched: bool
    fuel_permissive: bool
    fuel_command_pu: float
    alarm_active: bool
    trip_causes: tuple[str, ...]
    reset_accepted: bool


class SafetyInterlock:
    """Latched protective logic for an educational boiler simulation."""

    def __init__(self, config=None):
        self.config = config if config is not None else SafetyConfig()
        self._validate_config()
        self.trip_latched = False
        self.trip_causes = ()

    def _validate_config(self):
        c = self.config
        values = (
            c.low_low_level_pct,
            c.high_high_level_pct,
            c.low_low_pressure_pu,
            c.high_high_pressure_pu,
        )

        if not all(isfinite(value) for value in values):
            raise ValueError("Safety thresholds must be finite numbers")

        if not (
            0.0 <= c.low_low_level_pct < c.high_high_level_pct <= 100.0
        ):
            raise ValueError("Invalid drum-level trip thresholds")

        if not (
            0.0 <= c.low_low_pressure_pu < c.high_high_pressure_pu
        ):
            raise ValueError("Invalid pressure trip thresholds")

    def evaluate(
        self,
        level_pct,
        pressure_pu,
        *,
        sensors_valid=True,
        communication_ok=True,
        manual_reset=False,
    ):
        causes = []

        if not sensors_valid:
            causes.append("SENSOR_INVALID")

        if not communication_ok:
            causes.append("COMMUNICATION_LOSS")

        if sensors_valid:
            try:
                level = float(level_pct)
                pressure = float(pressure_pu)
            except (TypeError, ValueError, OverflowError):
                causes.append("SENSOR_INVALID")
            else:
                if not isfinite(level) or not isfinite(pressure):
                    causes.append("SENSOR_INVALID")
                else:
                    if not 0.0 <= level <= 100.0:
                        causes.append("LEVEL_SIGNAL_OUT_OF_RANGE")

                    if pressure < 0.0:
                        causes.append("PRESSURE_SIGNAL_OUT_OF_RANGE")

                    if level <= self.config.low_low_level_pct:
                        causes.append("LOW_LOW_DRUM_LEVEL")

                    if level >= self.config.high_high_level_pct:
                        causes.append("HIGH_HIGH_DRUM_LEVEL")

                    if pressure <= self.config.low_low_pressure_pu:
                        causes.append("LOW_LOW_PRESSURE")

                    if pressure >= self.config.high_high_pressure_pu:
                        causes.append("HIGH_HIGH_PRESSURE")

        causes = tuple(dict.fromkeys(causes))

        if causes:
            self.trip_latched = True
            self.trip_causes = tuple(
                dict.fromkeys(self.trip_causes + causes)
            )

        reset_accepted = False

        if self.trip_latched and manual_reset and not causes:
            self.trip_latched = False
            self.trip_causes = ()
            reset_accepted = True

        fuel_permissive = not self.trip_latched

        return SafetyStatus(
            trip_latched=self.trip_latched,
            fuel_permissive=fuel_permissive,
            fuel_command_pu=1.0 if fuel_permissive else 0.0,
            alarm_active=self.trip_latched,
            trip_causes=self.trip_causes,
            reset_accepted=reset_accepted,
        )
