# Boiler & Steam Utility Plant: DCS Digital Twin

A software-in-the-loop digital twin of a boiler and steam utility plant. A Python process model is closed in a loop with real PLC logic (OpenPLC, IEC 61131-3 Structured Text) over **Modbus TCP**, with a **FUXA SCADA/HMI** as the operator station. It implements the control structures used in industrial boiler plants: **three-element drum-level control**, **cascade pressure/combustion control**, and **simulated protective interlocks**.

> **Scope.** This is an educational simulation and control-system demonstrator. The process model is synthetic (not thermodynamically validated), the trip logic is not a certified SIS, and nothing here is intended for real plant equipment. See [Limitations](#limitations).

## At a glance

| | |
|---|---|
| **Domain** | Process control / DCS for boiler and steam utilities |
| **Control** | Single-element and three-element drum-level control; cascade pressure control with fuel-valve and air-damper outputs |
| **PLC layer** | OpenPLC Runtime, Structured Text, Modbus TCP holding-register interface (HR1124–HR1139) |
| **Operator layer** | FUXA SCADA/HMI with process displays and trends |
| **Integration** | Python bridge (`pymodbus`) with CSV tracing, reconnect handling, duplicate-instance protection |
| **Verification** | 54 unit tests (recorded run), bounded live-PLC disturbance tests, controller comparison by IAE |
| **Stack** | Python, NumPy/SciPy, OpenPLC, FUXA, Modbus TCP, Windows/PowerShell, VS Code |

<!-- ADD HERE: screenshots/ folder with (1) FUXA HMI overview, (2) disturbance-response trend plot, (3) controller comparison plot.
Example: ![FUXA HMI](docs/images/fuxa_overview.png) -->

## Why this project

In a real boiler, the drum-level and steam-pressure loops are strongly coupled and hard to control. This project builds those loops the way a DCS engineer would: the process model, the PLC controllers, the communication layer and the operator HMI are separate components that talk over an industrial protocol. The same PLC program could, in principle, be pointed at different process simulators or a hardware-in-the-loop rig.

## Architecture

```text
FUXA SCADA/HMI
      | Modbus TCP
      v
OpenPLC Runtime <----> Python–PLC bridge <----> Python boiler process model
      |                         |
      +---- PLC values          +---- CSV traces / validation scripts
```

- **Process model** (`model/`): drum water inventory and indicated level, **swell/shrink** effects, feedwater and steam flow, pressure, steam demand, fuel flow.
- **PLC** (`plc/`): control logic in Structured Text, running in OpenPLC Runtime.
- **Bridge** (`run_openplc_bridge.py`): advances the process each cycle using PLC outputs and writes simulated measurements back to PLC registers. Logs CSV traces, reconnects on Modbus loss and refuses to start a second instance.
- **HMI**: FUXA reads values exposed by the PLC; it never talks to the Python model directly, as in a real DCS.
- **Safety** (`safety/`): simulated trip/status handling with trip-reset command.

## Control strategies

**Drum level: three-element control.** Drum level is hard to control because of *swell and shrink*: a sudden steam-demand increase makes the indicated level rise briefly (steam bubbles expand) before it falls, so a level-only controller reacts the wrong way first. Three-element control combines **drum level** (feedback), **steam flow** (feedforward) and **feedwater flow** (inner loop), so feedwater tracks steam demand while level trims the mismatch. A single-element (level-only) controller is implemented for comparison.

**Pressure and combustion: cascade control.** The pressure controller sets the fuel demand, and the fuel-valve and air-damper outputs follow it. This is the cascade structure used for steam pressure control in firing systems.

**Interlocks (simulated).** Software-level trip and status logic with an operator reset (HR1139), for demonstration only.

## Results

All results below come from specific recorded runs. They are evidence for those scenarios, not general guarantees.

| Test | Scenario | Result |
|---|---|---|
| Offline controller comparison | Single-element vs three-element drum-level control, Python model | IAE **51.08 → 43.85 %·s** (about **14.1% lower** with three-element) |
| Live PLC disturbance | 30 s run, steam demand step **1.00 → 1.20 pu** at t = 5 s | Pressure dipped to about **0.995 pu**, recovered to about **1.005 pu**; no trip asserted |
| Bridge stability | Nominal manual-mode run, about 331 s | **3,301 cycles, 0 Modbus reconnects**, level held at 50.00% |
| Live closed-loop level | 120 s run, 50% setpoint | Level stayed within **48.56–51.10%**, final value **48.80%**, with a small residual offset at the end of the window (see [Known issues](#known-issues)) |
| Unit tests | `python -m unittest discover -s tests -v` | **54 passing** in the recorded run (re-run to verify on your machine) |

## Quick start

### 1. Standalone simulation (no PLC needed)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python run_simulation.py
```

Outputs: `runs/nominal.csv`, `runs/steam_demand_step.csv`, `runs/summary.txt`.

### 2. Tests

```powershell
python -m unittest discover -s tests -v
```

### 3. PLC-integrated workflow

Requires OpenPLC Runtime (with the Modbus TCP server enabled) and FUXA.

1. Deploy the Structured Text program from `plc/` to OpenPLC Runtime and start it.
2. Confirm the Modbus TCP endpoint is reachable (`scan_modbus_registers.py` can check this).
3. Start the bridge: `python run_openplc_bridge.py` (stop with `Ctrl+C`).
4. Open FUXA and confirm the displayed values match the PLC registers.
5. In a separate step, with the bridge in the required state, run a bounded test, for example `python run_openplc_disturbance.py`.

> **Do not run live tests that write PLC input registers while the bridge is also writing them.** Competing writes invalidate the test. `run_closed_loop_test.py` and `run_openplc_cascade_safety_validation.py` change demand, mode and other registers; they are not offline tests.

## Modbus register map

Holding registers **HR1124–HR1139**. Full details in [`docs/MODBUS_REGISTER_MAP.md`](docs/MODBUS_REGISTER_MAP.md).

| Register | Signal | Scaling |
|---|---|---|
| HR1124 | Heartbeat | Counter |
| HR1125 | Drum level | % × 100 |
| HR1126 | Feedwater flow | pu × 1000 |
| HR1127 | Steam flow | pu × 1000 |
| HR1128 | Drum-level setpoint | % × 100 |
| HR1129 | Manual valve command | % × 10 |
| HR1130 | Feedwater valve output | % × 10 |
| HR1131 | Automatic-mode selector | Integer state |
| HR1132 | Control/status word | Bit field |
| HR1133 | Pressure | pu × 1000 |
| HR1134 | Fuel flow | pu × 1000 |
| HR1135 | Steam demand | pu × 1000 |
| HR1136 | Fuel-valve output | % × 10 |
| HR1137 | Air-damper output | % × 10 |
| HR1138 | Pressure setpoint | pu × 1000 |
| HR1139 | Trip-reset command | Integer command |

Example: raw `5000` at HR1125 is `50.00 %`; raw `1000` at HR1126 is `1.000 pu`.

## Repository layout

```text
.
├── model/                  # Boiler process model
├── control/                # PID, single-element, three-element, cascade-pressure controllers
├── plc/                    # PLC Structured Text source
├── plc_interface/          # Register map and PLC adapter
├── safety/                 # Simulated protective logic
├── tests/                  # Model, controller, interface and safety tests
├── docs/                   # BUILD_PLAN.md, MODBUS_REGISTER_MAP.md
├── runs/                   # Recorded traces and outputs
├── run_simulation.py       # Standalone simulation
├── run_openplc_bridge.py   # Continuous Python–PLC bridge
├── run_openplc_disturbance.py
├── run_openplc_cascade_safety_validation.py
├── run_closed_loop_test.py
├── compare_controllers.py / evaluate_controllers.py / evaluate_pressure_control.py
└── analyze_disturbance_trace.py
```

Diagnostic scripts (`test_*.py`, `scan_*.py`, `verify_plc_state.py`) are development and bring-up utilities for the live PLC and Modbus link. Backup and recovery snapshots are development artifacts and are not needed to run the project.

## Known issues

- **Residual level offset in the live closed-loop run.** Level ended at 48.80% against a 50% setpoint after 120 s. Planned work: review integral action and anti-windup in the level loop, then re-run with a longer window.
- **Controller comparison is one scenario.** The 14.1% IAE improvement was measured in one model scenario with one tuning set; it has not been repeated across disturbance sizes.
- **No pinned dependency file yet.** Check imports before setting up a fresh environment.

## Limitations

- The process model is synthetic and not a validated thermodynamic model of a real boiler.
- The trip and interlock logic is simulated software, not a certified safety instrumented system, and makes no SIL or compliance claim.
- Offline tests, live PLC tests, communication checks and HMI checks each establish different things; a pass in one does not validate the others.
- Use for learning, experimentation and software-level engineering demonstration only.

## Roadmap

- Add integral anti-windup and re-tune the level loop to remove the residual offset
- Run controller comparison across several steam-demand disturbance magnitudes
- Add `requirements.txt`, CI for the unit tests and a demo video
- Add alarm management (high/low alarms with acknowledgement) in FUXA

## License

No license has been added yet. Until one is added, reuse and redistribution permissions should not be assumed.
