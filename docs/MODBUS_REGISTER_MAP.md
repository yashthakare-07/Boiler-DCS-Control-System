# Boiler DCS - Modbus TCP Register Map

Status: Draft - addresses must be verified against OpenPLC.

## Communication
- Protocol: Modbus TCP
- Host: 127.0.0.1
- Port: 502
- Register type: Holding registers
- Scaling: Integer engineering representation
- Register addressing: Zero-based addresses in the Python client

## Proposed process measurements
| Address | Tag | Description | Scale |
|---:|---|---|---|
| 0 | TEST_REGISTER | Communication test only | Raw integer |
| 10 | DRUM_LEVEL | Drum level | 0.01 % per count |
| 11 | DRUM_PRESSURE | Drum pressure | 0.001 pu per count |
| 12 | FEEDWATER_FLOW | Feedwater flow | 0.001 pu per count |
| 13 | STEAM_FLOW | Steam flow | 0.001 pu per count |
| 14 | FUEL_FLOW | Fuel flow | 0.001 pu per count |
| 15 | STEAM_DEMAND | Steam demand command | 0.001 pu per count |

## Proposed controller outputs
| Address | Tag | Description | Scale |
|---:|---|---|---|
| 30 | FEEDWATER_VALVE_CMD | Feedwater valve command | 0.1 % per count |
| 31 | FUEL_VALVE_CMD | Fuel valve command | 0.1 % per count |
| 32 | AIR_DAMPER_CMD | Combustion air damper command | 0.1 % per count |
| 33 | PUMP_COMMAND | Pump command | Enumerated value |

## Important
These addresses are proposed, not verified PLC mappings.
Do not use them for gateway communication until matching variables
and addresses have been configured and tested in OpenPLC.
The test register at address 0 must not be assumed to be a process tag.
