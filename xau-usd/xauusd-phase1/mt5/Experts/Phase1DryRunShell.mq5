#property strict
#property version   "1.000"
#property description "XAUUSD Phase 1 dry-run shell. Telemetry only."

#include <Phase1/Phase1Types.mqh>
#include <Phase1/Phase1Logger.mqh>
#include <Phase1/Phase1Risk.mqh>
#include <Phase1/Phase1Router.mqh>

input string InpRunId = "phase1-dry-run-v0.1";
input bool InpDryRunOnly = true;
input string InpTargetSymbol = "XAUUSD";
input double InpMaxSpreadPoints = 80.0;
input double InpMaxRiskPct = 0.25;
input bool InpAllowBreakoutRetest = false;
input string InpLogFileName = "phase1_dry_run_log.csv";

CPhase1CsvLogger g_logger;
CPhase1RiskGate g_risk_gate;
CPhase1Router g_router;
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
   }

   g_logger.Configure(InpLogFileName);
   g_risk_gate.Configure(InpMaxSpreadPoints, InpMaxRiskPct);
   g_router.Configure(InpAllowBreakoutRetest);

   Print("Phase1DryRunShell initialized: ", InpRunId);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   Print("Phase1DryRunShell stopped. reason=", reason);
}

void OnTick()
{
   if(_Symbol != InpTargetSymbol)
      return;

   datetime current_bar_time = iTime(_Symbol, PERIOD_M5, 0);
   if(current_bar_time <= 0)
      return;

   if(current_bar_time == g_last_m5_bar_time)
      return;
   g_last_m5_bar_time = current_bar_time;

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double spread_points = 0.0;
   if(point > 0.0)
      spread_points = (ask - bid) / point;

   bool spread_ok = g_risk_gate.SpreadAllowed(spread_points);

   Phase1Signal signal;
   g_router.SelectSignal(signal);

   if(!g_risk_gate.RiskAllowed(InpMaxRiskPct))
   {
      signal.blocked_reason = "risk_input_outside_phase1_limit";
   }
   else if(!spread_ok)
   {
      signal.blocked_reason = "spread_above_phase1_limit";
   }

   g_logger.WriteHeartbeat(
      InpRunId,
      "DRY_RUN",
      _Symbol,
      current_bar_time,
      bid,
      ask,
      spread_points,
      spread_ok,
      signal
   );
}
