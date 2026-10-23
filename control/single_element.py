
"""Single-element boiler drum-level controller."""

from control.pid import PIDController


class SingleElementController:
    """Use drum-level feedback to regulate feedwater flow.

    The PI controller generates a correction around the nominal
    feedwater command of 1.0 pu.

    Inputs:
        setpoint_pct: Desired drum level (%)
        measured_level_pct: Measured drum level (%)
        dt: Simulation time step (s)

    Output:
        Feedwater command in per-unit, limited to 0.0–1.5 pu.
    """

    def __init__(
        self,
        setpoint_pct=50.0,
        kp=0.08,
        ki=0.003,
        nominal_feedwater_pu=1.0,
    ):
        self.setpoint_pct = float(setpoint_pct)
        self.nominal_feedwater_pu = float(nominal_feedwater_pu)

        # PID output represents a correction to nominal feedwater.
        self.pid = PIDController(
            kp=kp,
            ki=ki,
            kd=0.0,
            output_min=-self.nominal_feedwater_pu,
            output_max=1.5 - self.nominal_feedwater_pu,
        )

    def reset(self):
        """Reset controller history for a fresh simulation."""
        self.pid.reset()

    def update(self, measured_level_pct, dt):
        """Calculate the feedwater command from measured drum level."""
        correction = self.pid.update(
            setpoint=self.setpoint_pct,
            measurement=measured_level_pct,
            dt=dt,
        )

        command = self.nominal_feedwater_pu + correction
        return max(0.0, min(1.5, command))
