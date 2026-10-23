PROGRAM Main
  VAR
    CycleTime_s : REAL := 0.02;
    LevelKp : REAL := 0.025;
    LevelKi : REAL := 0.001;
    FlowKp : REAL := 30.0;
    FlowKi : REAL := 10.0;
    PressureKp : REAL := 3.0;
    PressureKi : REAL := 0.15;
    FuelFlowKp : REAL := 30.0;
    FuelFlowKi : REAL := 10.0;
    DrumLevel_pct : REAL := 50.0;
    LevelSP_pct : REAL := 50.0;
    FeedwaterFlow_pu : REAL := 1.0;
    SteamFlow_pu : REAL := 1.0;
    DrumPressure_pu : REAL := 1.0;
    PressureSP_pu : REAL := 1.0;
    FuelFlow_pu : REAL := 1.0;
    SteamDemand_pu : REAL := 1.0;
    LevelError : REAL := 0.0;
    LevelIntegral : REAL := 0.0;
    LevelCorrection : REAL := 0.0;
    FeedwaterSP_pu : REAL := 1.0;
    FlowError : REAL := 0.0;
    FlowIntegral : REAL := 0.0;
    ValvePercent : REAL := 50.0;
    ValveUnsaturated : REAL := 50.0;
    PressureError : REAL := 0.0;
    PressureIntegral : REAL := 0.0;
    FuelFlowSP_pu : REAL := 1.0;
    FuelFlowError : REAL := 0.0;
    FuelFlowIntegral : REAL := 0.0;
    FuelValvePercent : REAL := 50.0;
    AirDamperPercent : REAL := 55.0;
    InputsValid : BOOL := TRUE;
    TripCauseActive : BOOL := FALSE;
    SafetyTripLatched : BOOL := FALSE;
    LevelSaturated : BOOL := FALSE;
    FuelSaturated : BOOL := FALSE;
  END_VAR
  VAR
    PLCHeartbeat AT %MW100 : INT := 0;
    DrumLevel_x100 AT %MW101 : INT := 5000;
    FeedwaterFlow_x1000 AT %MW102 : INT := 1000;
    SteamFlow_x1000 AT %MW103 : INT := 1000;
    LevelSP_x100 AT %MW104 : INT := 5000;
    ManualValve_x10 AT %MW105 : INT := 500;
    FeedwaterValve_x10 AT %MW106 : INT := 500;
    AutoMode_x10 AT %MW107 : INT := 0;
    StatusWord AT %MW108 : INT := 0;
    DrumPressure_x1000 AT %MW109 : INT := 1000;
    FuelFlow_x1000 AT %MW110 : INT := 1000;
    SteamDemand_x1000 AT %MW111 : INT := 1000;
    FuelValve_x10 AT %MW112 : INT := 500;
    AirDamper_x10 AT %MW113 : INT := 550;
    PressureSP_x1000 AT %MW114 : INT := 1000;
    TripReset_x10 AT %MW115 : INT := 0;
  END_VAR

  (* Decode scaled inputs *)
  DrumLevel_pct := INT_TO_REAL(DrumLevel_x100) / 100.0;
  LevelSP_pct := INT_TO_REAL(LevelSP_x100) / 100.0;
  FeedwaterFlow_pu := INT_TO_REAL(FeedwaterFlow_x1000) / 1000.0;
  SteamFlow_pu := INT_TO_REAL(SteamFlow_x1000) / 1000.0;
  DrumPressure_pu := INT_TO_REAL(DrumPressure_x1000) / 1000.0;
  FuelFlow_pu := INT_TO_REAL(FuelFlow_x1000) / 1000.0;
  SteamDemand_pu := INT_TO_REAL(SteamDemand_x1000) / 1000.0;
  PressureSP_pu := INT_TO_REAL(PressureSP_x1000) / 1000.0;


  (* Validate input ranges *)
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


  (* Simulated protective trip *)
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

  IF (TripReset_x10 > 0) AND NOT TripCauseActive THEN
      SafetyTripLatched := FALSE;
  END_IF;


  (* Three-element drum-level control *)
  LevelError := LevelSP_pct - DrumLevel_pct;
  LevelSaturated := FALSE;

  IF (AutoMode_x10 > 0) AND InputsValid AND NOT SafetyTripLatched THEN

      LevelIntegral := LevelIntegral
          + LevelKi * LevelError * CycleTime_s;

      IF LevelIntegral > 0.5 THEN
          LevelIntegral := 0.5;
      END_IF;

      IF LevelIntegral < -0.5 THEN
          LevelIntegral := -0.5;
      END_IF;

      LevelCorrection := LevelKp * LevelError + LevelIntegral;
      FeedwaterSP_pu := SteamFlow_pu + LevelCorrection;

      IF FeedwaterSP_pu > 1.5 THEN
          FeedwaterSP_pu := 1.5;
      END_IF;

      IF FeedwaterSP_pu < 0.0 THEN
          FeedwaterSP_pu := 0.0;
      END_IF;

      FlowError := FeedwaterSP_pu - FeedwaterFlow_pu;
      FlowIntegral := FlowIntegral + FlowKi * FlowError * CycleTime_s;

      IF FlowIntegral > 50.0 THEN
          FlowIntegral := 50.0;
      END_IF;

      IF FlowIntegral < -50.0 THEN
          FlowIntegral := -50.0;
      END_IF;

      ValveUnsaturated := 50.0 + FlowKp * FlowError + FlowIntegral;
      ValvePercent := ValveUnsaturated;

      IF ValvePercent > 100.0 THEN
          ValvePercent := 100.0;
          LevelSaturated := TRUE;
      END_IF;

      IF ValvePercent < 0.0 THEN
          ValvePercent := 0.0;
          LevelSaturated := TRUE;
      END_IF;

      FeedwaterValve_x10 := REAL_TO_INT(ValvePercent * 10.0);

  ELSIF AutoMode_x10 <= 0 THEN

      IF ManualValve_x10 > 1000 THEN
          ManualValve_x10 := 1000;
      END_IF;

      IF ManualValve_x10 < 0 THEN
          ManualValve_x10 := 0;
      END_IF;

      ValvePercent := INT_TO_REAL(ManualValve_x10) / 10.0;
      FeedwaterValve_x10 := ManualValve_x10;
      FeedwaterSP_pu := SteamFlow_pu;

  END_IF;


  (* Pressure master and fuel-flow controller *)
  FuelSaturated := FALSE;

  IF (AutoMode_x10 > 0) AND InputsValid AND NOT SafetyTripLatched THEN

      PressureError := PressureSP_pu - DrumPressure_pu;

      PressureIntegral := PressureIntegral
          + PressureKi * PressureError * CycleTime_s;

      IF PressureIntegral > 0.5 THEN
          PressureIntegral := 0.5;
      END_IF;

      IF PressureIntegral < -1.0 THEN
          PressureIntegral := -1.0;
      END_IF;

      FuelFlowSP_pu := SteamDemand_pu
          + PressureKp * PressureError
          + PressureIntegral;

      IF FuelFlowSP_pu > 1.5 THEN
          FuelFlowSP_pu := 1.5;
      END_IF;

      IF FuelFlowSP_pu < 0.0 THEN
          FuelFlowSP_pu := 0.0;
      END_IF;

      FuelFlowError := FuelFlowSP_pu - FuelFlow_pu;

      FuelFlowIntegral := FuelFlowIntegral
          + FuelFlowKi * FuelFlowError * CycleTime_s;

      IF FuelFlowIntegral > 50.0 THEN
          FuelFlowIntegral := 50.0;
      END_IF;

      IF FuelFlowIntegral < -50.0 THEN
          FuelFlowIntegral := -50.0;
      END_IF;

      FuelValvePercent := 50.0
          + FuelFlowKp * FuelFlowError
          + FuelFlowIntegral;

      IF FuelValvePercent > 100.0 THEN
          FuelValvePercent := 100.0;
          FuelSaturated := TRUE;
      END_IF;

      IF FuelValvePercent < 0.0 THEN
          FuelValvePercent := 0.0;
          FuelSaturated := TRUE;
      END_IF;

      FuelValve_x10 := REAL_TO_INT(FuelValvePercent * 10.0);

      (* Simulated air-to-fuel ratio command *)
      AirDamperPercent := 55.0 * FuelFlowSP_pu;

      IF AirDamperPercent > 100.0 THEN
          AirDamperPercent := 100.0;
      END_IF;

      IF AirDamperPercent < 0.0 THEN
          AirDamperPercent := 0.0;
      END_IF;

      AirDamper_x10 := REAL_TO_INT(AirDamperPercent * 10.0);

  ELSIF AutoMode_x10 <= 0 THEN

      FuelFlowSP_pu := SteamDemand_pu;
      FuelValvePercent := 50.0;
      FuelValve_x10 := 500;
      AirDamperPercent := 55.0;
      AirDamper_x10 := 550;

  END_IF;


  (* Simulated trip override *)
  IF SafetyTripLatched THEN
      FeedwaterValve_x10 := 0;
      FuelValve_x10 := 0;
      AirDamper_x10 := 0;
  END_IF;


  (* Status word bits:
     1 auto mode
     2 invalid inputs
     4 low level
     8 high level
     16 feedwater valve saturation
     32 simulated trip latched
     64 low pressure
     128 high pressure
     256 fuel permissive
  *)
  StatusWord := 0;

  IF AutoMode_x10 > 0 THEN
      StatusWord := StatusWord + 1;
  END_IF;

  IF NOT InputsValid THEN
      StatusWord := StatusWord + 2;
  END_IF;

  IF DrumLevel_pct <= 30.0 THEN
      StatusWord := StatusWord + 4;
  END_IF;

  IF DrumLevel_pct >= 70.0 THEN
      StatusWord := StatusWord + 8;
  END_IF;

  IF LevelSaturated THEN
      StatusWord := StatusWord + 16;
  END_IF;

  IF SafetyTripLatched THEN
      StatusWord := StatusWord + 32;
  END_IF;

  IF DrumPressure_pu <= 0.8 THEN
      StatusWord := StatusWord + 64;
  END_IF;

  IF DrumPressure_pu >= 1.2 THEN
      StatusWord := StatusWord + 128;
  END_IF;

  IF NOT SafetyTripLatched AND InputsValid THEN
      StatusWord := StatusWord + 256;
  END_IF;


  (* Increment heartbeat *)
  IF PLCHeartbeat >= 30000 THEN
      PLCHeartbeat := 0;
  ELSE
      PLCHeartbeat := PLCHeartbeat + 1;
  END_IF;
END_PROGRAM


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 1);
    PROGRAM instance0 WITH task0 : main;
  END_RESOURCE
END_CONFIGURATION
