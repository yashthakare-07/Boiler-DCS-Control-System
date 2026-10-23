import csv
from pathlib import Path

import matplotlib.pyplot as plt

# Directory where this script resides: .../BOILER DCS/runs
RUNS = Path(__file__).resolve().parent
PLOTS = RUNS / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)


def load_csv(filename: str):
    # Check if the file is in the script's directory (runs/)
    path = RUNS / filename
    if not path.is_file():
        # Fallback check in parent directory (.../BOILER DCS/)
        path = RUNS.parent / filename

    if not path.is_file():
        raise FileNotFoundError(
            f"Could not locate '{filename}' in '{RUNS}' or '{RUNS.parent}'."
        )

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def plot_signal(data, filename, column, ylabel, title, disturbance=False):
    time = [float(row["time_s"]) for row in data]
    values = [float(row[column]) for row in data]

    plt.figure(figsize=(10, 5))
    plt.plot(time, values, label=column, linewidth=1.8, color="#1f77b4")
    if disturbance:
        plt.axvline(10, color="crimson", linestyle="--", alpha=0.85, label="Steam demand step at 10 s")

    plt.xlabel("Time (s)", fontsize=11)
    plt.ylabel(ylabel, fontsize=11)
    plt.title(title, fontsize=13, fontweight="bold")
    plt.grid(True, alpha=0.3, linestyle=":")
    plt.legend(framealpha=0.9)
    plt.tight_layout()
    plt.savefig(PLOTS / filename, dpi=160)
    plt.close()


def main():
    nominal = load_csv("nominal.csv")
    disturbed = load_csv("steam_demand_step.csv")

    plot_signal(
        nominal,
        "nominal_level.png",
        "drum_level_pct",
        "Drum level (%)",
        "Nominal Boiler Drum Level",
    )
    plot_signal(
        disturbed,
        "disturbed_level.png",
        "drum_level_pct",
        "Drum level (%)",
        "Drum Level Under Steam-Demand Disturbance",
        disturbance=True,
    )
    plot_signal(
        disturbed,
        "disturbed_inventory.png",
        "inventory_pu",
        "Inventory (pu)",
        "Water Inventory Under Steam-Demand Disturbance",
        disturbance=True,
    )
    plot_signal(
        disturbed,
        "disturbed_pressure.png",
        "pressure_pu",
        "Pressure (pu)",
        "Pressure Under Steam-Demand Disturbance",
        disturbance=True,
    )

    # Combined Flow Comparison Plot
    plt.figure(figsize=(10, 5))
    time = [float(row["time_s"]) for row in disturbed]
    feedwater = [float(row["feedwater_flow_pu"]) for row in disturbed]
    steam = [float(row["steam_flow_pu"]) for row in disturbed]

    plt.plot(time, feedwater, label="Feedwater flow", linewidth=1.8, color="#2ca02c")
    plt.plot(time, steam, label="Steam flow", linewidth=1.8, color="#ff7f0e")
    plt.axvline(10, color="crimson", linestyle="--", alpha=0.85, label="Demand step at 10 s")

    plt.xlabel("Time (s)", fontsize=11)
    plt.ylabel("Flow (pu)", fontsize=11)
    plt.title("Feedwater and Steam Flow", fontsize=13, fontweight="bold")
    plt.grid(True, alpha=0.3, linestyle=":")
    plt.legend(framealpha=0.9)
    plt.tight_layout()
    plt.savefig(PLOTS / "disturbed_flows.png", dpi=160)
    plt.close()

    print("Stage 1 plots generated successfully:")
    print(f"Path: {PLOTS}")


if __name__ == "__main__":
    main()