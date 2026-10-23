PROGRAM main
  VAR
    CycleTime_s : REAL := 0.02;
    LevelKp : REAL := 0.025;
    LevelKi : REAL := 0.001;
    FlowKp : REAL := 30.0;
    FlowKi : REAL := 10.0;
    TrimLimit_pu : REAL := 0.5;
    DemandMax_pu : REAL := 2.0;
    SPMin_pct : REAL := 20.0;
    SPMax_pct : REAL := 80.0;
    AlarmLow_pct : REAL := 30.0;
    AlarmHigh_pct : REAL := 70.0;
    DrumLevel_pct : REAL := 50.0;
    LevelSetpoint_pct : REAL := 50.0;
    LevelError : REAL := 0.0;
    FeedwaterFlow_pu : REAL := 1.0;
    SteamFlow_pu : REAL := 1.0;
    LevelIntegral : REAL := 0.0;
    LevelTrialIntegral : REAL := 0.0;
    LevelTrim_pu : REAL := 0.0;
    FlowDemand_pu : REAL := 1.0;
    FlowError_pu : REAL := 0.0;
    FlowIntegral : REAL := 0.0;
    FlowTrialIntegral : REAL := 0.0;
    ValveUnsat : REAL := 50.0;
    ValvePercent : REAL := 50.0;
    ManualPercent : REAL := 50.0;
    ManualCmd_x10 : INT := 500;
    ValveSatHigh : BOOL := FALSE;
    ValveSatLow : BOOL := FALSE;
    InputsValid : BOOL := TRUE;
    AutoActive : BOOL := FALSE;
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
  END_VAR

  (* Convert register values into engineering units *)
  DrumLevel_pct := INT_TO_REAL(DrumLevel_x100) / 100.0;
  LevelSetpoint_pct := INT_TO_REAL(LevelSP_x100) / 100.0;
  FeedwaterFlow_pu := INT_TO_REAL(FeedwaterFlow_x1000) / 1000.0;
  SteamFlow_pu := INT_TO_REAL(SteamFlow_x1000) / 1000.0;

  (* Validate process input ranges *)
  InputsValid :=
      (DrumLevel_x100 >= 0) AND
      (DrumLevel_x100 <= 10000) AND
      (FeedwaterFlow_x1000 >= 0) AND
      (FeedwaterFlow_x1000 <= 2000) AND
      (SteamFlow_x1000 >= 0) AND
      (SteamFlow_x1000 <= 2000) AND
      (LevelSP_x100 >= 0) AND
      (LevelSP_x100 <= 10000);

  (* Limit operator setpoint *)
  IF LevelSetpoint_pct < SPMin_pct THEN
      LevelSetpoint_pct := SPMin_pct;
  END_IF;

  IF LevelSetpoint_pct > SPMax_pct THEN
      LevelSetpoint_pct := SPMax_pct;
  END_IF;

  (* Calculate level error *)
  LevelError := LevelSetpoint_pct - DrumLevel_pct;
  AutoActive := AutoMode_x10 > 0;

  (* Reset diagnostic flags each scan *)
  ValveSatHigh := FALSE;
  ValveSatLow := FALSE;
  StatusWord := 0;

  IF AutoActive THEN
      StatusWord := StatusWord + 1;
  END_IF;

  IF NOT InputsValid THEN
      (* Invalid simulated inputs: close the commanded valve *)
      StatusWord := StatusWord + 2;
      ValvePercent := 0.0;
      FeedwaterValve_x10 := 0;
      ValveSatLow := TRUE;

  ELSE
      IF AutoActive THEN

          (* OUTER LOOP: drum-level PI controller *)
          LevelTrialIntegral :=
              LevelIntegral + LevelKi * LevelError * CycleTime_s;

          IF LevelTrialIntegral > TrimLimit_pu THEN
              LevelTrialIntegral := TrimLimit_pu;
          END_IF;

          IF LevelTrialIntegral < -TrimLimit_pu THEN
              LevelTrialIntegral := -TrimLimit_pu;
          END_IF;

          LevelIntegral := LevelTrialIntegral;

          LevelTrim_pu :=
              LevelKp * LevelError + LevelIntegral;

          IF LevelTrim_pu > TrimLimit_pu THEN
              LevelTrim_pu := TrimLimit_pu;
          END_IF;

          IF LevelTrim_pu < -TrimLimit_pu THEN
              LevelTrim_pu := -TrimLimit_pu;
          END_IF;

          (* Three-element control:
             steam-flow feedforward + level correction *)
          FlowDemand_pu := SteamFlow_pu + LevelTrim_pu;

          IF FlowDemand_pu > DemandMax_pu THEN
              FlowDemand_pu := DemandMax_pu;
          END_IF;

          IF FlowDemand_pu < 0.0 THEN
              FlowDemand_pu := 0.0;
          END_IF;

          (* INNER LOOP: feedwater-flow PI controller *)
          FlowError_pu := FlowDemand_pu - FeedwaterFlow_pu;

          FlowTrialIntegral :=
              FlowIntegral + FlowKi * FlowError_pu * CycleTime_s;

          IF FlowTrialIntegral > 50.0 THEN
              FlowTrialIntegral := 50.0;
          END_IF;

          IF FlowTrialIntegral < -50.0 THEN
              FlowTrialIntegral := -50.0;
          END_IF;

          FlowIntegral := FlowTrialIntegral;

          ValveUnsat :=
              50.0 + FlowKp * FlowError_pu + FlowIntegral;

          ValvePercent := ValveUnsat;

          IF ValvePercent > 100.0 THEN
              ValvePercent := 100.0;
              ValveSatHigh := TRUE;
          END_IF;

          IF ValvePercent < 0.0 THEN
              ValvePercent := 0.0;
              ValveSatLow := TRUE;
          END_IF;

      ELSE
          (* MANUAL MODE: clamp operator command *)
          ManualCmd_x10 := ManualValve_x10;

          IF ManualCmd_x10 > 1000 THEN
              ManualCmd_x10 := 1000;
          END_IF;

          IF ManualCmd_x10 < 0 THEN
              ManualCmd_x10 := 0;
          END_IF;

          ManualPercent := INT_TO_REAL(ManualCmd_x10) / 10.0;
          ValvePercent := ManualPercent;

          (* Track controller states for mode transfer *)
          LevelIntegral :=
              FeedwaterFlow_pu - SteamFlow_pu
              - LevelKp * LevelError;

          FlowDemand_pu := SteamFlow_pu;
          FlowError_pu := FlowDemand_pu - FeedwaterFlow_pu;

          FlowIntegral :=
              ValvePercent - 50.0 - FlowKp * FlowError_pu;

          LevelTrim_pu := FeedwaterFlow_pu - SteamFlow_pu;
      END_IF;

      (* Convert commanded valve percentage to register units *)
      FeedwaterValve_x10 := REAL_TO_INT(ValvePercent * 10.0);
  END_IF;

  (* Status word bit values:
     1 = automatic mode
     2 = input fault
     4 = low drum level
     8 = high drum level
     16 = valve output saturated *)

  IF DrumLevel_pct < AlarmLow_pct THEN
      StatusWord := StatusWord + 4;
  END_IF;

  IF DrumLevel_pct > AlarmHigh_pct THEN
      StatusWord := StatusWord + 8;
  END_IF;

  IF ValveSatHigh OR ValveSatLow THEN
      StatusWord := StatusWord + 16;
  END_IF;

  (* Increment diagnostic heartbeat *)
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
