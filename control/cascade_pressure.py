"""Pressure controller for the reduced-order boiler digital twin."""

from control.pid import PIDController


class CascadePressureController:
    """PI pressure controller that adjusts boiler fuel demand.

    Pressure is measured in per-unit (pu). The controller output is a
    fuel command in pu, centered around the nominal fuel demand.

    This is an educational simulation controller, not validated
    industrial combustion-control logic.
    """

    def __init__(
        self,
        setpoint_pu=1.0,
        nominal_fuel_command_pu=1.0,
        pressure_kp=3.0,
        pressure_ki=0.15,
    ):
        self.setpoint_pu = float(setpoint_pu)
        self.nominal_fuel_command_pu = float(nominal_fuel_command_pu)

        if not 0.0 <= self.nominal_fuel_command_pu <= 1.5:
            raise ValueError(
                "nominal_fuel_command_pu must be between 0.0 and 1.5"
            )

        self.pressure_pid = PIDController(
            kp=pressure_kp,
            ki=pressure_ki,
            kd=0.0,
            output_min=-1.0,
            output_max=0.5,
        )

    def reset(self):
        """Reset pressure-controller history."""
        self.pressure_pid.reset()

    def update(self, measured_pressure_pu, dt):
        """Return a bounded fuel-demand command in per-unit."""
        correction_pu = self.pressure_pid.update(
            setpoint=self.setpoint_pu,
            measurement=measured_pressure_pu,
            dt=dt,
        )

        fuel_command_pu = (
            self.nominal_fuel_command_pu + correction_pu
        )

        return max(0.0, min(1.5, fuel_command_pu))
