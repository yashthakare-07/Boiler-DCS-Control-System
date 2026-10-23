
"""Compare single-element and three-element boiler level control."""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from model.boiler import BoilerModel
from control import SingleElementController, ThreeElementController

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
PLOTS = RUNS / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

DURATION_S = 60.0
DISTURBANCE_TIME_S = 10.0
LEVEL_SETPOINT_PCT = 50.0


def run_scenario(controller_type):
    """Run one controller with the same initial conditions and disturbance."""
    boiler = BoilerModel()
    dt = boiler.dt

    if controller_type == "single":
        controller = SingleElementController(
            setpoint_pct=LEVEL_SETPOINT_PCT
        )
    elif controller_type == "three":
        controller = ThreeElementController(
            setpoint_pct=LEVEL_SETPOINT_PCT
        )
    else:
        raise ValueError(f"Unknown controller: {controller_type}")

    records = []
    for _ in range(round(DURATION_S / dt)):
        state = boiler.state
        demand = (
            1.0 if state.time_s < DISTURBANCE_TIME_S else 1.2
        )

        if controller_type == "single":
            command = controller.update(
                measured_level_pct=state.drum_level_pct,
                dt=dt,
            )
        else:
            command = controller.update(
                measured_level_pct=state.drum_level_pct,
                measured_steam_flow_pu=state.steam_flow_pu,
                measured_feedwater_flow_pu=state.feedwater_flow_pu,
                dt=dt,
            )

        boiler.step(
            feedwater_command_pu=command,
            steam_demand_pu=demand,
            fuel_command_pu=1.0,
        )

        s = boiler.state
        records.append({
            "time_s": s.time_s,
            "steam_demand_pu": demand,
            "level_setpoint_pct": LEVEL_SETPOINT_PCT,
            "drum_level_pct": s.drum_level_pct,
            "level_error_pct": LEVEL_SETPOINT_PCT - s.drum_level_pct,
            "inventory_pu": s.inventory_pu,
            "pressure_pu": s.pressure_pu,
            "steam_flow_pu": s.steam_flow_pu,
            "feedwater_flow_pu": s.feedwater_flow_pu,
            "feedwater_command_pu": command,
            "indicated_swell_pct": s.indicated_swell_pct,
        })

    return records


def calculate_metrics(records):
    """Calculate level-control metrics over the complete run."""
    dt = records[1]["time_s"] - records[0]["time_s"]
    errors = [r["level_error_pct"] for r in records]
    post_step = [
        r for r in records if r["time_s"] >= DISTURBANCE_TIME_S
    ]

    # Settling time: first point after which all remaining errors
    # stay within +/-1 percentage point.
    settling_time = None
    for i, row in enumerate(post_step):
        if all(abs(r["level_error_pct"]) <= 1.0
               for r in post_step[i:]):
            settling_time = row["time_s"] - DISTURBANCE_TIME_S
            break

    post_errors = [r["level_error_pct"] for r in post_step]

    return {
        "IAE_pct_s": sum(abs(e) for e in errors) * dt,
        "maximum_absolute_level_error_pct": max(
            abs(e) for e in post_errors
        ),
        "positive_level_overshoot_pct": max(
            0.0, max(-e for e in post_errors)
        ),
        "final_level_pct": records[-1]["drum_level_pct"],
        "final_level_error_pct": records[-1]["level_error_pct"],
        "final_inventory_pu": records[-1]["inventory_pu"],
        "final_pressure_pu": records[-1]["pressure_pu"],
        "settling_time_after_step_s": settling_time,
    }


def write_csv(path, records):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)


def plot_comparison(single, three, column, ylabel, title, filename):
    plt.figure(figsize=(10, 5))

    for records, label in (
        (single, "Single-element"),
        (three, "Three-element"),
    ):
        plt.plot(
            [r["time_s"] for r in records],
            [r[column] for r in records],
            label=label,
        )

    plt.axvline(
        DISTURBANCE_TIME_S,
        linestyle="--",
        label="Steam-demand step",
    )

    if column == "drum_level_pct":
        plt.axhline(
            LEVEL_SETPOINT_PCT,
            linestyle=":",
            label="Level setpoint",
        )

    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS / filename, dpi=160)
    plt.close()


def main():
    print("Running single-element simulation...")
    single = run_scenario("single")

    print("Running three-element simulation...")
    three = run_scenario("three")

    write_csv(RUNS / "single_element.csv", single)
    write_csv(RUNS / "three_element.csv", three)

    metrics = {
        "single_element": calculate_metrics(single),
        "three_element": calculate_metrics(three),
    }

    with (RUNS / "controller_comparison.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "single_element", "three_element"])
        for name in metrics["single_element"]:
            writer.writerow([
                name,
                metrics["single_element"][name],
                metrics["three_element"][name],
            ])

    plot_comparison(
        single, three, "drum_level_pct", "Drum level (%)",
        "Drum-Level Control Comparison", "controller_level.png"
    )
    plot_comparison(
        single, three, "pressure_pu", "Pressure (pu)",
        "Boiler Pressure Comparison", "controller_pressure.png"
    )
    plot_comparison(
        single, three, "inventory_pu", "Inventory (pu)",
        "Boiler Inventory Comparison", "controller_inventory.png"
    )
    plot_comparison(
        single, three, "feedwater_flow_pu", "Feedwater flow (pu)",
        "Feedwater Flow Comparison", "controller_feedwater.png"
    )
    plot_comparison(
        single, three, "feedwater_command_pu", "Command (pu)",
        "Feedwater Command Comparison", "controller_command.png"
    )

    print("\nCONTROLLER COMPARISON RESULTS")
    print("=" * 55)

    for controller_name, values in metrics.items():
        print(f"\n{controller_name.replace('_', ' ').title()}")
        for name, value in values.items():
            display = (
                "Not settled during simulation"
                if value is None
                else f"{value:.4f}"
                if isinstance(value, float)
                else str(value)
            )
            print(f"  {name}: {display}")

    print("\nCSV files:", RUNS)
    print("Plots:", PLOTS)
    print("Comparison simulation completed.")


if __name__ == "__main__":
    main()
