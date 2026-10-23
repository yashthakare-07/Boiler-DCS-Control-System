# Boiler DCS Digital Twin — Build 01

Standalone software-only process model. Start with the process dynamics; PLC/Modbus/FUXA integration follows after validation.

Requirements: Python 3.10+; simulation and CSV export use only the standard library.

Run:
```powershell
python run_simulation.py
python -m unittest discover -s tests -v
```

Outputs: `runs/nominal.csv`, `runs/steam_demand_step.csv`, `runs/summary.txt`.

Educational synthetic model only. Not a validated thermodynamic model, certified safety system, or controller for real equipment.
