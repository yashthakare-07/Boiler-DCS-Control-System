PROGRAM main
VAR
    (* ---- Modbus-mapped registers ---- *)
    PLCHeartbeat        : INT AT %MW100 := 0;
    DrumLevel_x100      : INT AT %MW101 := 5000;   (* % x100, input  *)
    FeedwaterFlow_x1000 : INT AT %MW102 := 1000;   (* pu x1000, input *)
    SteamFlow_x1000     : INT AT %MW103 := 1000;   (* pu x1000, input *)
    LevelSP_x100        : INT AT %MW104 := 5000;   (* % x100, operator *)
    ManualValve_x10     : INT AT %MW105 := 500;    (* % x10, operator  *)
    FeedwaterValve_x10  : INT AT %MW106 := 500;    (* % x10, output    *)
    AutoMode_x10        : INT AT %MW107 := 0;      (* >0 = auto        *)
    StatusWord          : INT AT %MW108 := 0;      (* 1 auto, 2 input fault,
                                                      4 low lvl, 8 high lvl,
                                                      16 valve saturated *)

    (* ---- Tuning (match CycleTime_s to the OpenPLC task interval) ---- *)
    CycleTime_s  : REAL := 0.02;
    LevelKp      : REAL := 0.025;   (* pu flow per % level          *)
    LevelKi      : REAL := 0.001;   (* pu flow per (% level * s)    *)
    FlowKp       : REAL := 30.0;    (* % valve per pu flow          *)
    FlowKi       : REAL := 10.0;    (* % valve per (pu flow * s)    *)
    TrimLimit_pu : REAL := 0.5;
    DemandMax_pu : REAL := 2.0;
    SPMin_pct    : REAL := 20.0;
    SPMax_pct    : REAL := 80.0;
    AlarmLow_pct : REAL := 30.0;
    AlarmHigh_pct: REAL := 70.0;

    (* ---- Process values ---- *)
    DrumLevel_pct     : REAL := 50.0;
    LevelSetpoint_pct : REAL := 50.0;
    LevelError        : REAL := 0.0;
    FeedwaterFlow_pu  : REAL := 1.0;
    SteamFlow_pu      : REAL := 1.0;

    (* ---- Controller states ---- *)
    LevelIntegral      : REAL := 0.0;
    LevelTrialIntegral : REAL := 0.0;
    LevelTrim_pu       : REAL := 0.0;
    FlowDemand_pu      : REAL := 1.0;
    FlowError_pu       : REAL := 0.0;
    FlowIntegral       : REAL := 0.0;
    FlowTrialIntegral  : REAL := 0.0;
    ValveUnsat         : REAL := 50.0;
    ValvePercent       : REAL := 50.0;
    ManualPercent      : REAL := 50.0;
    ManualCmd_x10      : INT  := 500;

    ValveSatHigh : BOOL := FALSE;
    ValveSatLow  : BOOL := FALSE;
    InputsValid  : BOOL := TRUE;
    AutoActive   : BOOL := FALSE;
END_VAR

(* Calculate drum-level error in percentage points *)
LevelError :=
    INT_TO_REAL(LevelSP_x100 - DrumLevel_x100) / 100.0;

IF AutoMode_x10 > 0 THEN

    (* PI integral update for a 20 ms cyclic task *)
    IntegralTerm :=
        IntegralTerm + Ki * LevelError * CycleTime_s;

    (* Limit the integral contribution *)
    IF IntegralTerm > 50.0 THEN
        IntegralTerm := 50.0;
    END_IF;

    IF IntegralTerm < -50.0 THEN
        IntegralTerm := -50.0;
    END_IF;

    (* Calculate and limit the valve command *)
    ValvePercent := 50.0 + Kp * LevelError + IntegralTerm;

    IF ValvePercent > 100.0 THEN
        ValvePercent := 100.0;
    END_IF;

    IF ValvePercent < 0.0 THEN
        ValvePercent := 0.0;
    END_IF;

    FeedwaterValve_x10 := REAL_TO_INT(ValvePercent * 10.0);

ELSE

    (* Manual mode: track the integral for a smoother mode transfer *)
    IF ManualValve_x10 > 1000 THEN
        ManualValve_x10 := 1000;
    END_IF;

    IF ManualValve_x10 < 0 THEN
        ManualValve_x10 := 0;
    END_IF;

    FeedwaterValve_x10 := ManualValve_x10;

    IntegralTerm :=
        INT_TO_REAL(ManualValve_x10) / 10.0
        - 50.0
        - Kp * LevelError;

END_IF;

(* Increment a diagnostic heartbeat *)
IF PLCHeartbeat >= 30000 THEN
    PLCHeartbeat := 0;
ELSE
    PLCHeartbeat := PLCHeartbeat + 1;
END_IF;

END_PROGRAM := 50.0;
    END_IF;

    IF FlowIntegral_pct < -50.0 THEN
        FlowIntegral_pct := -50.0;
    END_IF;

    ValveUnclamped_pct :=
        50.0 + FlowKp * FlowError_pu + FlowIntegral_pct;

    ValvePercent := ValveUnclamped_pct;

    IF ValvePercent > 100.0 THEN
        ValvePercent := 100.0;
    END_IF;

    IF ValvePercent < 0.0 THEN
        ValvePercent := 0.0;
    END_IF;

    FeedwaterValve_x10 := REAL_TO_INT(ValvePercent * 10.0);

ELSE

    (* Manual mode: clamp the operator command *)
    IF ManualValve_x10 > 1000 THEN
        ManualValve_x10 := 1000;
    END_IF;

    IF ManualValve_x10 < 0 THEN
        ManualValve_x10 := 0;
    END_IF;

    ValvePercent := INT_TO_REAL(ManualValve_x10) / 10.0;
    FeedwaterValve_x10 := ManualValve_x10;

    (* Track controller states for a smoother mode transfer *)
    FeedwaterSP_pu := SteamFlow_pu;
    LevelCorrection_pu := FeedwaterFlow_pu - SteamFlow_pu;

    LevelIntegral_pu :=
        LevelCorrection_pu - LevelKp * LevelError_pct;

    FlowError_pu := FeedwaterSP_pu - FeedwaterFlow_pu;

    FlowIntegral_pct :=
        ValvePercent - 50.0 - FlowKp * FlowError_pu;

END_IF;

(* Diagnostic heartbeat *)
IF PLCHeartbeat >= 30000 THEN
    PLCHeartbeat := 0;
ELSE
    PLCHeartbeat := PLCHeartbeat + 1;
END_IF;

END_PROGRAM