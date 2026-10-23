# Build Plan

## Build 01 — Process model (included)
- Reduced-order deterministic process model
- Nominal equilibrium and steam-demand step tests
- State bounds and finite-value checks
- CSV exports

## Build 02 — Control
- Single-element level PID
- Three-element level control (level, steam flow, feedwater flow)
- PID output limits and anti-windup
- Compare both controllers under identical disturbances

## Build 03 — Protection and faults
- Low-low level and high-high pressure trips
- Sensor stale, bias, and stuck faults
- Cause/effect tests and manual reset conditions

## Build 04 — PLC/SCADA
- Confirm `%MW`/Modbus mapping
- Register contract and scaling
- Gateway heartbeat and stale-value handling
- FUXA trends, alarms, and operator commands

Simulation only. Do not connect to physical boiler equipment.
