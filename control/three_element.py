
"""Three-element boiler drum-level controller.

Elements:
1. Drum-level feedback: outer PI controller.
2. Steam-flow feedforward: anticipates changes in steam demand.
3. Feedwater-flow feedback: inner PI controller tracks required flow.
"""

from control.pid import PIDController


class ThreeElementController:
    """Three-element drum-level controller.

    All flows use per-unit (pu) values. Drum level uses percent.
    The returned value is the feedwater valve command in pu.
    """

    def __init__(
        self,
        setpoint_pct=50.0,
        level_kp=0.025,
        level_ki=0.001,
        flow_kp=1.5,
        flow_ki=0.8,
    ):
        self.setpoint_pct = float(setpoint_pct)

        # Outer loop: level error produces a flow trim.
        self.level_pid = PIDController(
            kp=level_kp,
            ki=level_ki,
            kd=0.0,
            output_min=-0.5,
            output_max=0.5,
        )

        # Inner loop: feedwater flow error adjusts the valve command.
        self.flow_pid = PIDController(
            kp=flow_kp,
            ki=flow_ki,
            kd=0.0,
            output_min=-1.5,
            output_max=1.5,
        )

    def reset(self):
        """Reset both controller loops."""
        self.level_pid.reset()
        self.flow_pid.reset()

    def update(
        self,
        measured_level_pct,
        measured_steam_flow_pu,
        measured_feedwater_flow_pu,
        dt,
    ):
        """Calculate the feedwater valve command."""

        # Element 1: level controller produces a trim in pu.
        level_trim_pu = self.level_pid.update(
            setpoint=self.setpoint_pct,
            measurement=measured_level_pct,
            dt=dt,
        )

        # Element 2: steam-flow feedforward plus level trim.
        desired_feedwater_flow_pu = (
            float(measured_steam_flow_pu) + level_trim_pu
        )

        # The desired flow must stay within the plant's flow range.
        desired_feedwater_flow_pu = max(
            0.0, min(1.5, desired_feedwater_flow_pu)
        )

        # Element 3: inner flow loop tracks the desired feedwater flow.
        flow_correction = self.flow_pid.update(
            setpoint=desired_feedwater_flow_pu,
            measurement=measured_feedwater_flow_pu,
            dt=dt,
        )

        # Use measured flow as the nominal valve-command estimate.
        command = float(measured_feedwater_flow_pu) + flow_correction

        return max(0.0, min(1.5, command))
