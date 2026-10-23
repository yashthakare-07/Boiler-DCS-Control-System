"""Convert boiler simulation values into the project's Modbus register image."""

from plc_interface.register_map import (
    build_register_image,
    encode_trip_causes,
)


def build_boiler_registers(
    state,
    feedwater_command_pu,
    requested_fuel_command_pu,
    safety_status,
    simulation_running=True,
):
    """Build a complete register image from model and controller state."""

    effective_fuel_command = (
        safety_status.fuel_command_pu
        if safety_status.trip_latched
        else requested_fuel_command_pu
    )

    values = {
        "drum_level_pct": state.drum_level_pct,
        "pressure_pu": state.pressure_pu,
        "steam_flow_pu": state.steam_flow_pu,
        "feedwater_flow_pu": state.feedwater_flow_pu,
        "fuel_flow_pu": state.fuel_flow_pu,
        "heat_duty_pu": state.heat_duty_pu,
        "feedwater_command_pu": feedwater_command_pu,
        "fuel_command_pu": effective_fuel_command,
        "trip_latched": safety_status.trip_latched,
        "fuel_permissive": safety_status.fuel_permissive,
        "alarm_active": safety_status.alarm_active,
        "trip_cause_mask": encode_trip_causes(
            safety_status.trip_causes
        ),
        "simulation_status": int(simulation_running),
    }

    return build_register_image(values)
