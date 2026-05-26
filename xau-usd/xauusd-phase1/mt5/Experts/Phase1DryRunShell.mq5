#property strict
#property version   "1.000"
#property description "XAUUSD Phase 1 dry-run shell. Telemetry only."

#include <Phase1/Phase1Types.mqh>
#include <Phase1/Phase1Logger.mqh>
#include <Phase1/Phase1Risk.mqh>
#include <Phase1/Phase1Router.mqh>
#include <Phase1/Phase1MarketData.mqh>
#include <Phase1/Phase1Session.mqh>
#include <Phase1/Phase1Execution.mqh>
#include <Phase1/Phase1News.mqh>
#include <Phase1/Phase1Dashboard.mqh>
#include <Phase1/Phase1FeatureEngine.mqh>
#include <Phase1/Phase1ServerTime.mqh>
#include <Phase1/Phase1Magic.mqh>
#include <Phase1/Phase1Lifecycle.mqh>
#include <Phase1/Phase1BreakoutRetest.mqh>

input string InpRunId = "phase1-dry-run-v0.6";
input bool InpDryRunOnly = true;
input string InpTargetSymbol = "XAUUSD";
input double InpMaxSpreadPoints = 80.0;
input double InpMaxRiskPct = 0.25;
input double InpDailyLossLimitPct = 2.0;
input double InpWeeklyLossLimitPct = 5.0;
input double InpMonthlyLossLimitPct = 10.0;
input double InpSimulatedDailyPnlPct = 0.0;
input double InpSimulatedWeeklyPnlPct = 0.0;
input double InpSimulatedMonthlyPnlPct = 0.0;
input bool InpManualRiskLock = false;
input bool InpObserveBreakoutRetest = true;
input bool InpObserveSwingBreakoutRetest = true;
input bool InpManualNewsLockdown = false;
input int InpExpectedLocalUtcOffsetMinutes = 330;
input int InpMaxClockDriftSeconds = 300;
input string InpDecisionLogFileName = "decision_log.csv";
input string InpStartupLogFileName = "startup_log.csv";
input string InpShutdownLogFileName = "shutdown_log.csv";

CPhase1CsvLogger g_logger;
CPhase1RiskGate g_risk_gate;
CPhase1Router g_router;
CPhase1MarketDataEngine g_market_data;
CPhase1SessionEngine g_session_engine;
CPhase1ExecutionGuard g_execution_guard;
CPhase1NewsGuard g_news_guard;
CPhase1Dashboard g_dashboard;
CPhase1FeatureEngine g_feature_engine;
CPhase1ServerTimeValidator g_server_time_validator;
CPhase1MagicNumberAllocator g_magic_allocator;
CPhase1ExpertLifecycleManager g_lifecycle_manager;
CPhase1BreakoutRetestObserver g_breakout_retest_observer;
CPhase1BreakoutRetestObserver g_swing_breakout_retest_observer;
datetime g_last_m5_bar_time = 0;

int OnInit()
{
   if(!InpDryRunOnly)
   {
      Print("Phase1DryRunShell refused to start because dry-run mode is locked.");
      return INIT_FAILED;
   }

   if(_Symbol != InpTargetSymbol)
   {
      Print("Phase1DryRunShell attached to ", _Symbol, " but target is ", InpTargetSymbol);
      return INIT_FAILED;
   }

   g_logger.Configure(InpDecisionLogFileName, InpStartupLogFileName, InpShutdownLogFileName);
   g_risk_gate.Configure(
      InpMaxSpreadPoints,
      InpMaxRiskPct,
      InpDailyLossLimitPct,
      InpWeeklyLossLimitPct,
      InpMonthlyLossLimitPct,
      InpSimulatedDailyPnlPct,
      InpSimulatedWeeklyPnlPct,
      InpSimulatedMonthlyPnlPct,
      InpManualRiskLock
   );
   bool magic_namespace_ok = g_magic_allocator.ValidateNamespace();
   if(!magic_namespace_ok)
   {
      Print("Phase1DryRunShell refused to start because magic-number namespace is invalid.");
      return INIT_FAILED;
   }

   g_router.Configure(
      InpObserveBreakoutRetest,
      InpObserveSwingBreakoutRetest,
      g_magic_allocator.BreakoutRetestMagic(),
      g_magic_allocator.SwingBreakoutRetestMagic()
   );
   g_execution_guard.Configure(InpMaxSpreadPoints);
   g_news_guard.Configure(InpManualNewsLockdown);
   g_server_time_validator.Configure(InpExpectedLocalUtcOffsetMinutes, InpMaxClockDriftSeconds);
   g_lifecycle_manager.Configure(InpObserveBreakoutRetest, InpObserveSwingBreakoutRetest);
   g_breakout_retest_observer.Configure(false);
   g_swing_breakout_retest_observer.Configure(true);
   Phase1MarketSnapshot startup_snapshot;
   Phase1ServerTimeStatus startup_time_status;
   if(g_market_data.BuildSnapshot(_Symbol, startup_snapshot))
      g_server_time_validator.Validate(startup_snapshot, startup_time_status);
   else
      Phase1ResetServerTimeStatus(startup_time_status);
   g_logger.WriteStartup(
      InpRunId,
      _Symbol,
      InpDryRunOnly,
      InpObserveBreakoutRetest,
      InpObserveSwingBreakoutRetest,
      InpMaxSpreadPoints,
      InpMaxRiskPct,
      InpDailyLossLimitPct,
      InpWeeklyLossLimitPct,
      InpMonthlyLossLimitPct,
      InpManualRiskLock,
      magic_namespace_ok,
      startup_time_status
   );
   EventSetTimer(1);

   Print("Phase1DryRunShell initialized: ", InpRunId);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   g_dashboard.Clear();
   g_logger.WriteShutdown(InpRunId, _Symbol, reason, g_last_m5_bar_time);
   Print("Phase1DryRunShell stopped. reason=", reason);
}

void OnTick()
{
}

void OnTimer()
{
   if(_Symbol != InpTargetSymbol)
      return;

   Phase1MarketSnapshot snapshot;
   if(!g_market_data.BuildSnapshot(_Symbol, snapshot))
      return;

   if(snapshot.m5_bar_time == g_last_m5_bar_time)
      return;
   g_last_m5_bar_time = snapshot.m5_bar_time;

   g_execution_guard.RecordSpread(snapshot.spread_points);

   Phase1Signal signal;
   g_router.SelectSignal(signal);

   Phase1Decision decision;
   Phase1ResetDecision(decision);
   decision.run_id = InpRunId;
   decision.lifecycle_state = "DRY_RUN";
   decision.market = snapshot;
   decision.session_state = g_session_engine.Detect(snapshot.utc_time);
   decision.news_state = g_news_guard.Evaluate(snapshot.utc_time);
   decision.execution_state = g_execution_guard.Evaluate(snapshot);
   decision.risk_state = g_risk_gate.Evaluate(InpMaxRiskPct, decision.risk_details);
   g_feature_engine.Build(snapshot.symbol_name, snapshot.point, decision.features);
   g_server_time_validator.Validate(snapshot, decision.server_time);
   g_breakout_retest_observer.Evaluate(snapshot.symbol_name, snapshot.point, decision.breakout_retest);
   g_swing_breakout_retest_observer.Evaluate(snapshot.symbol_name, snapshot.point, decision.swing_breakout_retest);
   decision.regime_state = g_router.ClassifyRegime(
      snapshot,
      decision.session_state,
      decision.execution_state,
      decision.news_state
   );
   Phase1NormalizeSignalFromObservers(decision, signal);
   decision.allowed_expert = "none";
   decision.would_have_allowed_experts = g_router.WouldHaveAllowedExperts();
   decision.br_lifecycle_state = g_lifecycle_manager.BreakoutRetestStateText();
   decision.sbr_lifecycle_state = g_lifecycle_manager.SwingBreakoutRetestStateText();
   decision.expert_lifecycle_state = decision.br_lifecycle_state;
   decision.magic_namespace_ok = g_magic_allocator.ValidateNamespace();
   decision.trade_permission = false;
   decision.dry_run = true;
   decision.block_reason = Phase1BlockReason(decision, decision.signal);

   g_logger.WriteDecision(decision);
   g_dashboard.Render(decision);
}

void Phase1NormalizeSignalFromObservers(Phase1Decision &decision, const Phase1Signal &router_signal)
{
   Phase1ResetSignal(decision.signal);
   decision.signal.blocked_reason = router_signal.blocked_reason;
   if(decision.signal.blocked_reason == "")
      decision.signal.blocked_reason = "phase1_dry_run_only";

   if(decision.breakout_retest.would_signal)
   {
      Phase1FillSignalFromObservation(
         decision.signal,
         "breakout_retest",
         g_magic_allocator.BreakoutRetestMagic(),
         decision.breakout_retest
      );
      return;
   }

   if(decision.swing_breakout_retest.would_signal)
   {
      Phase1FillSignalFromObservation(
         decision.signal,
         "swing_breakout_retest_v0",
         g_magic_allocator.SwingBreakoutRetestMagic(),
         decision.swing_breakout_retest
      );
   }
}

void Phase1FillSignalFromObservation(
   Phase1Signal &signal,
   const string expert_name,
   const int magic_number,
   const Phase1BreakoutRetestObservation &observation
)
{
   signal.expert_name = expert_name;
   signal.magic_number = magic_number;
   signal.direction = Phase1DirectionFromObserverText(observation.direction_text);
   signal.entry_price = observation.entry_price;
   signal.stop_loss = observation.stop_loss;
   signal.take_profit = observation.take_profit;
   signal.risk_pct = InpMaxRiskPct;
   signal.reason_code = observation.reason_code;
   signal.blocked_reason = "phase1_dry_run_only";
}

Phase1SignalDirection Phase1DirectionFromObserverText(const string direction_text)
{
   if(direction_text == "LONG")
      return PHASE1_SIGNAL_LONG;
   if(direction_text == "SHORT")
      return PHASE1_SIGNAL_SHORT;
   return PHASE1_SIGNAL_NONE;
}

string Phase1BlockReason(const Phase1Decision &decision, const Phase1Signal &signal)
{
   if(!decision.magic_namespace_ok)
      return "magic_namespace_invalid";
   if(!decision.server_time.clock_ok)
      return decision.server_time.status_text;
   if(decision.news_state != PHASE1_NEWS_NO_RISK)
      return Phase1NewsText(decision.news_state);
   if(decision.execution_state != PHASE1_EXECUTION_OK)
      return Phase1ExecutionText(decision.execution_state);
   if(decision.risk_state != PHASE1_RISK_NORMAL)
      return Phase1RiskText(decision.risk_state);
   if(signal.blocked_reason != "")
      return signal.blocked_reason;
   return "phase1_dry_run_only";
}
