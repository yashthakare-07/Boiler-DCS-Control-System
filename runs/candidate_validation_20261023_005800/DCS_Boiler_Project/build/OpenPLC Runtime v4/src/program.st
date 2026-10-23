PROGRAM main
  VAR
    DrumLevel_pct : REAL := 50.0;
    LevelSP_pct : REAL := 50.0;
    FeedwaterFlow_pu : REAL := 1.0;
    SteamFlow_pu : REAL := 1.0;
    LevelError_pct : REAL := 0.0;
    LevelKp : REAL := 0.02;
    LevelKi : REAL := 0.001;
    LevelIntegral_pu : REAL := 0.0;
    LevelCorrection_pu : REAL := 0.0;
    FeedwaterSP_pu : REAL := 1.0;
    FlowError_pu : REAL := 0.0;
    FlowKp : REAL := 50.0;
    FlowKi : REAL := 8.0;
    FlowIntegral_pct : REAL := 0.0;
    CycleTime_s : REAL := 0.02;
    ValvePercent : REAL := 50.0;
    ValveUnclamped_pct : REAL := 50.0;
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
  END_VAR

  (* Convert integer register values to engineering units *)
  DrumLevel_pct := INT_TO_REAL(DrumLevel_x100) / 100.0;
  LevelSP_pct := INT_TO_REAL(LevelSP_x100) / 100.0;
  FeedwaterFlow_pu := INT_TO_REAL(FeedwaterFlow_x1000) / 1000.0;
  SteamFlow_pu := INT_TO_REAL(SteamFlow_x1000) / 1000.0;

  LevelError_pct := LevelSP_pct - DrumLevel_pct;

  IF AutoMode_x10 > 0 THEN

      (* OUTER LOOP: drum-level feedback.
         Its output is a correction to steam-flow feedforward. *)
      LevelIntegral_pu :=
          LevelIntegral_pu + LevelKi * LevelError_pct * CycleTime_s;

      IF LevelIntegral_pu > 0.5 THEN
          LevelIntegral_pu := 0.5;
      END_IF;

      IF LevelIntegral_pu < -0.5 THEN
          LevelIntegral_pu := -0.5;
      END_IF;

      LevelCorrection_pu :=
          LevelKp * LevelError_pct + LevelIntegral_pu;

      (* Three-element feedwater setpoint:
         steam flow + level correction *)
      FeedwaterSP_pu := SteamFlow_pu + LevelCorrection_pu;

      IF FeedwaterSP_pu > 1.5 THEN
          FeedwaterSP_pu := 1.5;
      END_IF;

      IF FeedwaterSP_pu < 0.0 THEN
          FeedwaterSP_pu := 0.0;
      END_IF;

      (* INNER LOOP: feedwater-flow feedback *)
      FlowError_pu := FeedwaterSP_pu - FeedwaterFlow_pu;

      FlowIntegral_pct :=
          FlowIntegral_pct + FlowKi * FlowError_pu * CycleTime_s;

      IF FlowIntegral_pct > 50.0 THEN
          FlowIntegral_pct := 50.0;
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


CONFIGURATION Config0

  RESOURCE Res0 ON PLC
    TASK task0(INTERVAL := T#20ms,PRIORITY := 1);
    PROGRAM instance0 WITH task0 : main;
  END_RESOURCE
END_CONFIGURATION
