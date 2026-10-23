from dataclasses import dataclass
from math import isfinite

@dataclass
class BoilerState:
    time_s: float = 0.0
    inventory_pu: float = 1.0
    drum_level_pct: float = 50.0
    pressure_pu: float = 1.0
    heat_duty_pu: float = 1.0
    feedwater_flow_pu: float = 1.0
    steam_flow_pu: float = 1.0
    fuel_flow_pu: float = 1.0
    indicated_swell_pct: float = 0.0

DEFAULT_CONFIG = {
    "dt_s": 0.1, "inventory_gain": 0.01, "inventory_min": 0.0,
    "inventory_max": 1.5, "valve_tau_s": 1.5, "steam_tau_s": 1.0,
    "heat_tau_s": 12.0, "pressure_tau_s": 10.0, "swell_tau_s": 2.0,
    "fuel_to_heat_gain": 1.0, "pressure_heat_gain": 0.2,
    "pressure_steam_gain": 0.15, "swell_steam_gain": 8.0,
    "swell_pressure_gain": 4.0, "inventory_to_level_gain": 50.0,
    "blowdown_pu": 0.0,
}

class BoilerModel:
    """Deterministic reduced-order model with 1 pu nominal equilibrium."""
    def __init__(self, config=None):
        self.config = dict(DEFAULT_CONFIG)
        if config:
            self.config.update(config)
        self.dt = float(self.config["dt_s"])
        if self.dt <= 0:
            raise ValueError("dt_s must be positive")
        self.state = BoilerState()

    @staticmethod
    def _approach(x, target, dt, tau):
        return target if tau <= 0 else x + (target-x)*min(dt/tau, 1.0)

    @staticmethod
    def _clip(x, lo, hi):
        return max(lo, min(hi, x))

    def step(self, feedwater_command_pu=1.0, steam_demand_pu=1.0, fuel_command_pu=1.0):
        c, s, dt = self.config, self.state, self.dt
        fw = self._clip(float(feedwater_command_pu), 0.0, 1.5)
        steam = self._clip(float(steam_demand_pu), 0.0, 1.5)
        fuel = self._clip(float(fuel_command_pu), 0.0, 1.5)
        s.feedwater_flow_pu = self._approach(s.feedwater_flow_pu, fw, dt, c["valve_tau_s"])
        s.steam_flow_pu = self._approach(s.steam_flow_pu, steam, dt, c["steam_tau_s"])
        s.fuel_flow_pu = self._approach(s.fuel_flow_pu, fuel, dt, c["valve_tau_s"])
        rate = c["inventory_gain"] * (s.feedwater_flow_pu - s.steam_flow_pu - c["blowdown_pu"])
        s.inventory_pu = self._clip(s.inventory_pu + rate*dt, c["inventory_min"], c["inventory_max"])
        s.heat_duty_pu = self._approach(s.heat_duty_pu, s.fuel_flow_pu*c["fuel_to_heat_gain"], dt, c["heat_tau_s"])
        p_target = 1.0 + c["pressure_heat_gain"]*(s.heat_duty_pu-1.0) - c["pressure_steam_gain"]*(s.steam_flow_pu-1.0)
        s.pressure_pu = self._approach(s.pressure_pu, max(0.0, p_target), dt, c["pressure_tau_s"])
        swell_target = c["swell_steam_gain"]*(s.steam_flow_pu-1.0) + c["swell_pressure_gain"]*(s.pressure_pu-1.0)
        s.indicated_swell_pct = self._approach(s.indicated_swell_pct, swell_target, dt, c["swell_tau_s"])
        s.drum_level_pct = self._clip(50.0 + (s.inventory_pu-1.0)*c["inventory_to_level_gain"] + s.indicated_swell_pct, 0.0, 100.0)
        s.time_s += dt
        for key, value in vars(s).items():
            if not isfinite(value):
                raise FloatingPointError(f"Non-finite state {key}={value}")
        return s
