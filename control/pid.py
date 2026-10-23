
"""PID controller with output saturation and conditional anti-windup."""

from dataclasses import dataclass


@dataclass
class PIDController:
    """Discrete-time PID controller.

    The controller uses error = setpoint - measurement.
    Output is constrained to [output_min, output_max].
    Conditional integration limits integral windup.
    """

    kp: float
    ki: float
    kd: float = 0.0
    output_min: float = 0.0
    output_max: float = 1.5
    derivative_tau: float = 0.0

    def __post_init__(self):
        if self.output_min >= self.output_max:
            raise ValueError("output_min must be less than output_max")
        if self.derivative_tau < 0:
            raise ValueError("derivative_tau cannot be negative")

        self.reset()

    def reset(self, output: float = 0.0) -> None:
        """Reset controller history."""
        self.integral = 0.0
        self.previous_error = None
        self.filtered_derivative = 0.0
        self.last_output = self._clamp(output)

    def _clamp(self, value: float) -> float:
        return max(self.output_min, min(self.output_max, value))

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        """Calculate a bounded controller output for one time step."""
        if dt <= 0:
            raise ValueError("dt must be greater than zero")

        error = float(setpoint) - float(measurement)

        if self.previous_error is None:
            raw_derivative = 0.0
        else:
            raw_derivative = (error - self.previous_error) / dt

        # Optional first-order filtering of the derivative term.
        if self.derivative_tau > 0:
            alpha = dt / (self.derivative_tau + dt)
            self.filtered_derivative += alpha * (
                raw_derivative - self.filtered_derivative
            )
        else:
            self.filtered_derivative = raw_derivative

        proportional = self.kp * error
        derivative = self.kd * self.filtered_derivative

        # Trial output before updating the integral term.
        trial_integral = self.integral + error * dt
        trial_unbounded = (
            proportional + self.ki * trial_integral + derivative
        )
        trial_output = self._clamp(trial_unbounded)

        # Integrate when unsaturated, or when the error pushes the
        # saturated output back toward the permitted range.
        pushing_further_high = (
            trial_unbounded > self.output_max and error * self.ki > 0
        )
        pushing_further_low = (
            trial_unbounded < self.output_min and error * self.ki < 0
        )

        if not (pushing_further_high or pushing_further_low):
            self.integral = trial_integral

        unbounded = (
            proportional + self.ki * self.integral + derivative
        )
        output = self._clamp(unbounded)

        self.previous_error = error
        self.last_output = output
        return output
