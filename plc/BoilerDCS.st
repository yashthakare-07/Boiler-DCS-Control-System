(*
    Boiler DCS Digital Twin
    PLC interface variable declarations - draft

    These declarations must be incorporated into the OpenPLC
    project and mapped to the verified Modbus server variables.
*)

PROGRAM BoilerDCS
VAR
    (* Process measurements: scaled integer values *)
    DrumLevel_x100       : INT := 5000;
    DrumPressure_x1000   : INT := 1000;
    FeedwaterFlow_x1000  : INT := 1000;
    SteamFlow_x1000      : INT := 1000;
    FuelFlow_x1000       : INT := 1000;
    SteamDemand_x1000    : INT := 1000;

    (* Controller outputs: 0 to 1000 represents 0 to 100.0% *)
    FeedwaterValve_x10   : INT := 500;
    FuelValve_x10        : INT := 500;
    AirDamper_x10        : INT := 500;

    (* Pump command: 0 = stop, 1 = pump A, 2 = pump B *)
    PumpCommand          : INT := 0;

    (* Communication diagnostics *)
    PythonHeartbeat      : INT := 0;
    PLCHeartbeat         : INT := 0;
END_VAR

(* Controller logic will be implemented in the next stage. *)

END_PROGRAM
