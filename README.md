# Boiler and Steam Utility Plant DCS Digital Twin

A software-in-the-loop digital twin for studying boiler process dynamics, PLC-based control, industrial communication, SCADA/HMI integration, and disturbance-response analysis using open-source tooling.

**Scope:** This is an educational software simulation and control-system demonstrator. It is not a thermodynamically validated boiler model, a certified safety instrumented system, or a controller for real plant equipment.

## Project overview

The project couples a Python-based boiler process model to PLC logic running in OpenPLC Runtime. A Python bridge exchanges process measurements and control outputs over Modbus TCP. FUXA is used as the operator-facing SCADA/HMI layer, and CSV traces plus Python tests support analysis of the simulated response.

The model represents drum water inventory and indicated level, swell/shrink effects, feedwater and steam flow, pressure, steam demand, fuel flow, and fuel/air command outputs.

### Architecture

```text
FUXA SCADA/HMI
      | Modbus TCP
      v
OpenPLC Runtime <----> Python–PLC bridge <----> Python boiler process model
      |                         |
      +---- PLC values          +---- CSV traces / validation scripts
```

The bridge advances the process simulation using PLC control outputs and writes simulated measurements back to the PLC register interface. FUXA reads values exposed by the PLC. The model, PLC, bridge, HMI, and analysis scripts are separate components.

## Main capabilities

- **Process simulation:** water-inventory and drum-level dynamics, swell/shrink effects, flow variables, pressure, steam demand, and combustion-related variables.
- **Drum-level control concepts:** single-element feedback and three-element control using drum level, steam flow, and feedwater flow.
- **Pressure/combustion control:** cascade pressure-control concepts with fuel-valve and air-damper command outputs.
- **PLC integration:** OpenPLC Runtime with a documented Modbus TCP holding-register interface.
- **Process/PLC bridge:** continuous Python–PLC data exchange, CSV tracing, reconnect handling, and duplicate-instance protection.
- **SCADA/HMI:** FUXA-based process displays and trends using values exposed by the PLC.
- **Verification and analysis:** Python unit tests, bounded live PLC checks, controller-comparison scripts, and trace-analysis utilities.
- **Simulated safety behavior:** software-level trip/status handling for demonstration only.

## Technology stack

| Component | Technology |
|---|---|
| Process model and analysis | Python, NumPy/SciPy where used by the relevant modules |
| PLC programming/runtime | OpenPLC Editor and OpenPLC Runtime |
| PLC language | Structured Text (IEC 61131-3 style) |
| Communication | Modbus TCP |
| Integration bridge | Python and `pymodbus` |
| Operator station | FUXA SCADA/HMI |
| Verification | Python `unittest` |
| Recorded evidence | CSV traces, text logs, and analysis scripts |
| Development tools | Windows, PowerShell, and Visual Studio Code |

## Repository layout

The repository has evolved beyond the initial standalone simulator. Key source and documentation paths include:

```text
.
├── model/                         # Boiler process model
├── control/                       # PID, single-element, three-element,
│                                  # and cascade-pressure control modules
├── plc/                           # PLC Structured Text source
├── plc_interface/                 # Register map and PLC adapter
├── safety/                        # Simulated safety-related logic
├── tests/                          # Model, controller, interface, and safety tests
├── docs/
│   ├── BUILD_PLAN.md
│   └── MODBUS_REGISTER_MAP.md
├── runs/                          # Recorded test traces, outputs, and snapshots
├── run_simulation.py              # Standalone simulation entry point
├── run_openplc_bridge.py          # Continuous Python–PLC bridge
├── run_openplc_disturbance.py     # Disturbance test runner
├── run_openplc_cascade_safety_validation.py
├── run_closed_loop_test.py        # Live closed-loop diagnostic
├── compare_controllers.py
├── evaluate_controllers.py
├── evaluate_pressure_control.py
├── analyze_disturbance_trace.py
└── README.md
```

The repository also contains recovery snapshots, diagnostic logs, and backup artifacts from development. These are not required for every run and may contain machine-specific runtime details.

## Requirements

- Python 3.10 or newer for the documented standalone simulation workflow.
- A project-local virtual environment is recommended.
- OpenPLC Runtime and FUXA are required for the PLC-integrated workflow.
- The Python–PLC bridge and live integration checks require a reachable OpenPLC Modbus TCP endpoint.
- Additional Python packages may be required by the PLC bridge, model, plotting, or analysis scripts. The exact dependency list should be checked before setting up a fresh environment; a complete pinned requirements file is not established in this README.

The project was developed in a Windows/PowerShell environment. Recorded runtime IP addresses and ports are deployment-specific and should not be treated as permanent settings.

## Running the standalone simulation

From the repository root, create/activate your Python environment and run:

```powershell
python run_simulation.py
```

The initial standalone workflow documents output files such as:

- `runs/nominal.csv`
- `runs/steam_demand_step.csv`
- `runs/summary.txt`

Exact outputs depend on the current version of the script. This standalone simulation does not require a live PLC connection.

## Running the Python test suite

From the repository root:

```powershell
python -m unittest discover -s tests -v
```

A previously recorded project run reported **54 passing tests**. This is historical evidence for the test set and code state at that time, not a guarantee that all tests pass on every checkout or machine. Re-run the command to verify the current environment.

## PLC-integrated workflow

The PLC-integrated workflow requires the PLC program to be deployed and running in OpenPLC Runtime, with the configured Modbus TCP interface enabled.

At a high level:

1. Start OpenPLC Runtime and confirm its Modbus TCP endpoint is reachable.
2. Confirm that the deployed PLC program exposes the expected register map.
3. Start the Python–PLC bridge using the local configuration.
4. Open the FUXA HMI and verify that the displayed engineering values correspond to the PLC register values.
5. Run a bounded disturbance-validation script only when its required PLC mode, bridge state, and register ownership conditions are satisfied.
6. Inspect the generated CSV trace and console output before drawing conclusions about response performance.

The bridge is intended to run continuously until stopped with `Ctrl+C` or until it exits on an error. Do not run a live test that writes to the same PLC input registers concurrently with the bridge: competing writes can invalidate a test. Follow the script-specific preconditions and cleanup behavior.

**Live-test caution:** Scripts with names such as `run_closed_loop_test.py` and `run_openplc_cascade_safety_validation.py` interact with the PLC and may change demand, mode, or other registers. Do not treat them as offline-only tests.

## Modbus register interface

The documented holding-register map uses HR1124–HR1139. The meanings and scaling documented for this project are:

| Register | Signal | Scaling / interpretation |
|---|---|---|
| HR1124 | Heartbeat | Counter |
| HR1125 | Drum level | Percentage × 100 |
| HR1126 | Feedwater flow | pu × 1000 |
| HR1127 | Steam flow | pu × 1000 |
| HR1128 | Drum-level setpoint | Percentage × 100 |
| HR1129 | Manual valve command | Percentage × 10 |
| HR1130 | Feedwater valve output | Percentage × 10 |
| HR1131 | Automatic-mode selector | Integer state |
| HR1132 | Control/status word | Status/bit field |
| HR1133 | Pressure | pu × 1000 |
| HR1134 | Fuel flow | pu × 1000 |
| HR1135 | Steam demand | pu × 1000 |
| HR1136 | Fuel-valve output | Percentage × 10 |
| HR1137 | Air-damper output | Percentage × 10 |
| HR1138 | Pressure setpoint | pu × 1000 |
| HR1139 | Trip-reset command | Integer command |

For example, raw value `5000` at HR1125 corresponds to `50.00%`, and raw value `1000` at HR1126 corresponds to `1.000 pu`. Consult [docs/MODBUS_REGISTER_MAP.md](docs/MODBUS_REGISTER_MAP.md) and the deployed PLC program before relying on the map; register addressing and deployment configuration must agree.

## Recorded validation evidence

The development notes contain the following results for specific test scenarios.

### Offline controller comparison

In one Python-model scenario, the three-element strategy recorded an integrated absolute error (IAE) of **43.8526 %·s**, compared with **51.0829 %·s** for the single-element strategy. This is approximately a **14.1% lower IAE** in that scenario. The result is model-specific and depends on the model and controller tuning; it is not a universal guarantee or proof that the live PLC achieves the same improvement.

### Bounded PLC/process-coupling disturbance test

A recorded 30-second validation stepped steam demand from **1.00 pu to 1.20 pu** at 5 seconds. In that run, the logged pressure dipped to approximately **0.995 pu** and recovered to approximately **1.005 pu**. The trace reported no asserted trip during that scenario. These observations apply only to the recorded test and do not verify every operating or trip condition.

### Closed-loop diagnostic limitation

A separate 120-second live closed-loop diagnostic recorded a peak drum-level indication of **51.102%**, a minimum of **48.557%**, and a final value of **48.796%** against a 50% setpoint. It therefore did **not** demonstrate complete level recovery to setpoint by the end of that test window.

### Bridge connectivity check

One nominal manual-mode bridge run lasted approximately **331 seconds**, completed **3,301 cycles**, and reported **zero Modbus reconnects**. The drum-level sample remained at 50.00% during that nominal run. This supports connectivity under the tested nominal conditions; it does not demonstrate automatic disturbance rejection.

These results are included to make the current evidence and limitations explicit. They are not a substitute for reproducing the tests against the current code and runtime configuration.

## Safety and model limitations

- The process model is synthetic and is not a validated thermodynamic model of a real boiler.
- The safety/trip behavior is simulated software logic, not a certified safety instrumented system.
- The project has not established a safety-integrity certification, compliance claim, physical shutdown capability, or approval for use on real equipment.
- Offline unit tests, controller simulations, live PLC tests, communication checks, and HMI checks establish different things. A pass in one category does not imply that every other category has been validated.
- Use this repository for learning, experimentation, and software-level engineering demonstration only.

## Further documentation

- [Build plan](docs/BUILD_PLAN.md)
- [Modbus register map](docs/MODBUS_REGISTER_MAP.md)

## License

No license is asserted by this README. Unless a license file is added to the repository, reuse and redistribution permissions should not be assumed.
