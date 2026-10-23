(*
  BOILER DCS DIGITAL TWIN — EXTENDED PLC CANDIDATE
  Intended for disposable validation copy only. NOT yet compiled or runtime-validated.
  Simulation-only control logic; not a certified boiler/burner safety system.

  Existing holding-register addresses retained:
    1124 heartbeat; 1125 level x100; 1126 feedwater flow x1000;
    1127 steam flow x1000; 1128 level setpoint x100; 1129 manual valve x10;
    1130 feedwater valve output x10; 1131 automatic mode.

  Proposed additional holding-register addresses (must be verified in a test copy):
    1132 status word; 1133 pressure x1000; 1134 fuel flow x1000;
    1135 steam-demand command x1000; 1136 fuel-valve output x10;
    1137 air-damper output x10; 1138 pressure setpoint x1000;
    1139 trip-reset command.
*)
PROGRAM main
VAR
    (* Existing verified process interface: %MW100..%MW107 -> HR1124..1131 *)
    PLCHeartbeat         : INT AT %MW100 := 0;
    DrumLevel_x100       : INT AT %MW101 := 5000;
    FeedwaterFlow_x1000  : INT AT %MW102 := 1000;
    SteamFlow_x1000      : INT AT %MW103 := 1000;
    LevelSP_x100         : INT AT %MW104 := 5000;
    ManualValve_x10      : INT AT %MW105 := 500;
    FeedwaterValve_x10   : INT AT %MW106 := 500;
    AutoMode_x10         : INT AT %MW107 := 0;

    (* Extension interface: %MW108..%MW115 -> proposed HR1132..1139 *)
    StatusWord           : INT AT %MW108 := 0;
    DrumPressure_x1000   : INT AT %MW109 := 1000;
    FuelFlow_x1000       : INT AT %MW110 := 1000;
    SteamDemand_x1000    : INT AT %MW111 := 1000;
    FuelValve_x10        : INT AT %MW112 := 500;
    AirDamper_x10        : INT AT %MW113 := 550;
    PressureSP_x1000     : INT AT %MW114 := 1000;
    TripReset_x10        : INT AT %MW115 := 0;

    (* Engineering-unit values *)
    DrumLevel_pct        : REAL := 50.0;
    LevelSP_pct          : REAL := 50.0;
    FeedwaterFlow_pu     : REAL := 1.0;
    SteamFlow_pu         : REAL := 1.0;
    DrumPressure_pu      : REAL := 1.0;
    PressureSP_pu        : REAL := 1.0;
    FuelFlow_pu          : REAL := 1.0;
    SteamDemand_pu       : REAL := 1.0;

    (* Three-element drum-level controller *)
    LevelError_pct       : REAL := 0.0;
    LevelKp               : REAL := 0.02;
    LevelKi               : REAL := 0.001;
    LevelIntegral_pu     : REAL := 0.0;
    LevelCorrection_pu   : REAL := 0.0;
    FeedwaterSP_pu       : REAL := 1.0;
    FlowError_pu         : REAL := 0.0;
    FlowKp                : REAL := 50.0;
    FlowKi                : REAL := 8.0;
    FlowIntegral_pct     : REAL := 0.0;
    ValvePercent         : REAL := 50.0;
    ValveUnclamped_pct   : REAL := 50.0;

    (* Pressure master -> fuel-flow demand -> fuel-valve output *)
    PressureError_pu     : REAL := 0.0;
    PressureKp            : REAL := 3.0;
    PressureKi            : REAL := 0.15;
    PressureIntegral_pu  : REAL := 0.0;
    FuelFlowSP_pu        : REAL := 1.0;
    FuelFlowError_pu     : REAL := 0.0;
    FuelValveKp           : REAL := 30.0;
    FuelValveKi           : REAL := 10.0;
    FuelValveIntegral_pct: REAL := 0.0;
    FuelValvePercent     : REAL := 50.0;
    FuelValveUnclamped_pct : REAL := 50.0;
    AirDamperPercent     : REAL := 55.0;

    (* Diagnostics / simulated protective logic *)
    CycleTime_s          : REAL := 0.02;
    InputsValid          : BOOL := TRUE;
    TripCauseActive      : BOOL := FALSE;
    SafetyTripLatched    : BOOL := FALSE;
END_VAR

(* Decode process inputs and operator setpoints. *)
DrumLevel_pct := INT_TO_REAL(DrumLevel_x100) / 100.0;
LevelSP_pct := INT_TO_REAL(LevelSP_x100) / 100.0;
FeedwaterFlow_pu := INT_TO_REAL(FeedwaterFlow_x1000) / 1000.0;
SteamFlow_pu := INT_TO_REAL(SteamFlow_x1000) / 1000.0;
DrumPressure_pu := INT_TO_REAL(DrumPressure_x1000) / 1000.0;
FuelFlow_pu := INT_TO_REAL(FuelFlow_x1000) / 1000.0;
SteamDemand_pu := INT_TO_REAL(SteamDemand_x1000) / 1000.0;
PressureSP_pu := INT_TO_REAL(PressureSP_x1000) / 1000.0;

(* Reject invalid/out-of-range measurements and setpoints. *)
InputsValid := TRUE;
IF (DrumLevel_x100 < 0) OR (DrumLevel_x100 > 10000) THEN
    InputsValid := FALSE;
END_IF;
IF (FeedwaterFlow_x1000 < 0) OR (FeedwaterFlow_x1000 > 2000) THEN
    InputsValid := FALSE;
END_IF;
IF (SteamFlow_x1000 < 0) OR (SteamFlow_x1000 > 2000) THEN
    InputsValid := FALSE;
END_IF;
IF (DrumPressure_x1000 < 0) OR (DrumPressure_x1000 > 2000) THEN
    InputsValid := FALSE;
END_IF;
IF (FuelFlow_x1000 < 0) OR (FuelFlow_x1000 > 2000) THEN
    InputsValid := FALSE;
END_IF;
IF (SteamDemand_x1000 < 0) OR (SteamDemand_x1000 > 2000) THEN
    InputsValid := FALSE;
END_IF;
IF (LevelSP_x100 < 2000) OR (LevelSP_x100 > 8000) THEN
    InputsValid := FALSE;
END_IF;
IF (PressureSP_x1000 < 500) OR (PressureSP_x1000 > 1500) THEN
    InputsValid := FALSE;
END_IF;

(* Latching simulation trip. Reset is accepted only when the initiating
   simulated conditions and input-validity fault have cleared. *)
TripCauseActive := NOT InputsValid;
IF DrumLevel_pct <= 20.0 THEN
    TripCauseActive := TRUE;
END_IF;
IF DrumLevel_pct >= 80.0 THEN
    TripCauseActive := TRUE;
END_IF;
IF DrumPressure_pu <= 0.5 THEN
    TripCauseActive := TRUE;
END_IF;
IF DrumPressure_pu >= 1.5 THEN
    TripCauseActive := TRUE;
END_IF;

IF TripCauseActive THEN
    SafetyTripLatched := TRUE;
END_IF;
IF (TripReset_x10 > 0) AND (NOT TripCauseActive) THEN
    SafetyTripLatched := FALSE;
END_IF;

LevelError_pct := LevelSP_pct - DrumLevel_pct;

(* C1: three-element drum-level/feedwater control. *)
IF (AutoMode_x10 > 0) AND InputsValid THEN
    LevelIntegral_pu := LevelIntegral_pu + LevelKi * LevelError_pct * CycleTime_s;
    IF LevelIntegral_pu > 0.5 THEN LevelIntegral_pu := 0.5; END_IF;
    IF LevelIntegral_pu < -0.5 THEN LevelIntegral_pu := -0.5; END_IF;

    LevelCorrection_pu := LevelKp * LevelError_pct + LevelIntegral_pu;
    FeedwaterSP_pu := SteamFlow_pu + LevelCorrection_pu;
    IF FeedwaterSP_pu > 1.5 THEN FeedwaterSP_pu := 1.5; END_IF;
    IF FeedwaterSP_pu < 0.0 THEN FeedwaterSP_pu := 0.0; END_IF;

    FlowError_pu := FeedwaterSP_pu - FeedwaterFlow_pu;
    FlowIntegral_pct := FlowIntegral_pct + FlowKi * FlowError_pu * CycleTime_s;
    IF FlowIntegral_pct > 50.0 THEN FlowIntegral_pct := 50.0; END_IF;
    IF FlowIntegral_pct < -50.0 THEN FlowIntegral_pct := -50.0; END_IF;

    ValveUnclamped_pct := 50.0 + FlowKp * FlowError_pu + FlowIntegral_pct;
    ValvePercent := ValveUnclamped_pct;
    IF ValvePercent > 100.0 THEN ValvePercent := 100.0; END_IF;
    IF ValvePercent < 0.0 THEN ValvePercent := 0.0; END_IF;
    FeedwaterValve_x10 := REAL_TO_INT(ValvePercent * 10.0);
ELSIF AutoMode_x10 <= 0 THEN
    IF ManualValve_x10 > 1000 THEN ManualValve_x10 := 1000; END_IF;
    IF ManualValve_x10 < 0 THEN ManualValve_x10 := 0; END_IF;
    ValvePercent := INT_TO_REAL(ManualValve_x10) / 10.0;
    FeedwaterValve_x10 := ManualValve_x10;
    FeedwaterSP_pu := SteamFlow_pu;
    LevelCorrection_pu := FeedwaterFlow_pu - SteamFlow_pu;
    LevelIntegral_pu := LevelCorrection_pu - LevelKp * LevelError_pct;
    FlowError_pu := FeedwaterSP_pu - FeedwaterFlow_pu;
    FlowIntegral_pct := ValvePercent - 50.0 - FlowKp * FlowError_pu;
END_IF;

(* C2: pressure master produces fuel-flow demand, with steam demand
   feedforward. Inner fuel-flow PI drives the fuel valve. The air-damper
   output is a simple simulated ratio-following command, not an air-flow loop. *)
IF (AutoMode_x10 > 0) AND InputsValid AND (NOT SafetyTripLatched) THEN
    PressureError_pu := PressureSP_pu - DrumPressure_pu;
    PressureIntegral_pu := PressureIntegral_pu + PressureKi * PressureError_pu * CycleTime_s;
    IF PressureIntegral_pu > 0.5 THEN PressureIntegral_pu := 0.5; END_IF;
    IF PressureIntegral_pu < -1.0 THEN PressureIntegral_pu := -1.0; END_IF;

    FuelFlowSP_pu := SteamDemand_pu + PressureKp * PressureError_pu + PressureIntegral_pu;
    IF FuelFlowSP_pu > 1.5 THEN FuelFlowSP_pu := 1.5; END_IF;
    IF FuelFlowSP_pu < 0.0 THEN FuelFlowSP_pu := 0.0; END_IF;

    FuelFlowError_pu := FuelFlowSP_pu - FuelFlow_pu;
    FuelValveIntegral_pct := FuelValveIntegral_pct + FuelValveKi * FuelFlowError_pu * CycleTime_s;
    IF FuelValveIntegral_pct > 50.0 THEN FuelValveIntegral_pct := 50.0; END_IF;
    IF FuelValveIntegral_pct < -50.0 THEN FuelValveIntegral_pct := -50.0; END_IF;

    FuelValveUnclamped_pct := 50.0 + FuelValveKp * FuelFlowError_pu + FuelValveIntegral_pct;
    FuelValvePercent := FuelValveUnclamped_pct;
    IF FuelValvePercent > 100.0 THEN FuelValvePercent := 100.0; END_IF;
    IF FuelValvePercent < 0.0 THEN FuelValvePercent := 0.0; END_IF;
    FuelValve_x10 := REAL_TO_INT(FuelValvePercent * 10.0);

    AirDamperPercent := 55.0 * FuelFlowSP_pu;
    IF AirDamperPercent > 100.0 THEN AirDamperPercent := 100.0; END_IF;
    IF AirDamperPercent < 0.0 THEN AirDamperPercent := 0.0; END_IF;
    AirDamper_x10 := REAL_TO_INT(AirDamperPercent * 10.0);
ELSIF AutoMode_x10 <= 0 THEN
    (* Stable simulated manual baseline; no manual fuel/air faceplate yet. *)
    FuelFlowSP_pu := SteamDemand_pu;
    FuelValvePercent := 50.0;
    FuelValve_x10 := 500;
    AirDamperPercent := 55.0;
    AirDamper_x10 := 550;
    PressureIntegral_pu := 0.0;
    FuelValveIntegral_pct := 0.0;
END_IF;

(* Simulated protective override: fuel command forced closed on latched trip. *)
IF SafetyTripLatched THEN
    FuelValve_x10 := 0;
    AirDamper_x10 := 0;
END_IF;

(* Status word bits: 1 auto, 2 invalid input, 4 low level alarm,
   8 high level alarm, 16 feedwater-valve saturation, 32 latched trip,
   64 low-pressure alarm, 128 high-pressure alarm, 256 fuel permissive. *)
StatusWord := 0;
IF AutoMode_x10 > 0 THEN StatusWord := StatusWord + 1; END_IF;
IF NOT InputsValid THEN StatusWord := StatusWord + 2; END_IF;
IF DrumLevel_pct <= 30.0 THEN StatusWord := StatusWord + 4; END_IF;
IF DrumLevel_pct >= 70.0 THEN StatusWord := StatusWord + 8; END_IF;
IF (ValvePercent >= 99.9) OR (ValvePercent <= 0.1) THEN
    StatusWord := StatusWord + 16;
END_IF;
IF SafetyTripLatched THEN StatusWord := StatusWord + 32; END_IF;
IF DrumPressure_pu <= 0.8 THEN StatusWord := StatusWord + 64; END_IF;
IF DrumPressure_pu >= 1.2 THEN StatusWord := StatusWord + 128; END_IF;
IF NOT SafetyTripLatched THEN StatusWord := StatusWord + 256; END_IF;

(* Diagnostic heartbeat. *)
IF PLCHeartbeat >= 30000 THEN
    PLCHeartbeat := 0;
ELSE
    PLCHeartbeat := PLCHeartbeat + 1;
END_IF;

END_PROGRAM
