#property strict
#property version   "1.00"
#property description "WR50 demo-only experimental breakout-retest 1R exit lane. Non-canonical, no live authorization."

#include <WR50/WR50_Common.mqh>

input bool   InpExperimentalDemoOnly = true;
input bool   InpAllowDemoTrading = false;
input string InpOwnerAuthorizationToken = "";
input string InpRequiredOwnerAuthorizationToken = "";
input string InpExperimentId = "WR50_20260604_A";
input string InpRunId = "R240604A";
input string InpAllowedSymbol = "XAUUSD";
input bool   InpAllowSymbolSuffix = true;
input double InpFixedLot = 0.0;
input int    InpMaxSpreadPoints = 50;
input int    InpMaxTradesPerDay = 5;
input int    InpMaxOpenPositionsForThisEA = 1;
input int    InpMaxOpenWR50PositionsTotal = 3;
input double InpMaxDailyLossAccountCurrency = 100.0;
input bool   InpAllowNettingAccountForDemoExperiment = false;
input bool   InpAllowSharedSymbolExposure = false;
input bool   InpRequireDemoServerName = true;
input bool   InpRequireRuntimeRegistryFile = true;
input string InpRuntimeRegistryFile = "WR50\\wr50_runtime_registry.csv";
input bool   InpRequireAccountAllowlist = false;
input string InpAccountAllowlistFile = "WR50\\wr50_account_allowlist.csv";
input int    InpRolloverStartHour = 22;
input int    InpRolloverStartMinute = 0;
input int    InpRolloverEndHour = 23;
input int    InpRolloverEndMinute = 15;
input string InpManualBlackoutFile = "WR50\\wr50_blackout_windows.csv";
input int    InpPendingExpiryM5Bars = 5;

const string EA_ID = "wr50_e1r0";
const string EA_NAME = "WR50_BreakoutExit1R_v0";
const string EA_VERSION = "v0";
const string EA_SHORT_CODE = "E1R0";
const string STRATEGY_FAMILY = "breakout_retest_wr50_experimental";
const int EA_MAGIC = WR50_E1R0_ACTIVE_MAGIC;
const int EA_MAGIC_START = WR50_E1R0_MAGIC_START;
const int EA_MAGIC_END = WR50_E1R0_MAGIC_END;
datetime g_last_completed_m5_bar = 0;

int OnInit()
{
   string reason = "";
   WR50_LogStartup(EA_ID, EA_SHORT_CODE, EA_VERSION, InpExperimentId, InpRunId, EA_MAGIC, "INIT_START", "demo_only_non_canonical");
   if(!WR50_ValidateAccountGuard(InpExperimentalDemoOnly,
                                 InpAllowDemoTrading,
                                 InpOwnerAuthorizationToken,
                                 InpRequiredOwnerAuthorizationToken,
                                 EA_ID,
                                 EA_NAME,
                                 EA_MAGIC,
                                 EA_MAGIC_START,
                                 EA_MAGIC_END,
                                 InpAllowedSymbol,
                                 InpAllowSymbolSuffix,
                                 InpRequireDemoServerName,
                                 InpRequireRuntimeRegistryFile,
                                 InpRuntimeRegistryFile,
                                 InpAccountAllowlistFile,
                                 InpRequireAccountAllowlist,
                                 InpAllowNettingAccountForDemoExperiment,
                                 reason))
   {
      WR50_LogStartup(EA_ID, EA_SHORT_CODE, EA_VERSION, InpExperimentId, InpRunId, EA_MAGIC, "INIT_FAILED", reason);
      Comment("WR50 INIT FAILED: ", reason);
      return INIT_FAILED;
   }
   WR50_LogStartup(EA_ID, EA_SHORT_CODE, EA_VERSION, InpExperimentId, InpRunId, EA_MAGIC, "INIT_OK", reason);
   Comment("WR50 E1R0 demo experiment armed. Non-canonical.");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   Comment("");
}

void OnTick()
{
   datetime completed_bar = iTime(_Symbol, PERIOD_M5, 1);
   if(completed_bar == 0 || completed_bar == g_last_completed_m5_bar)
      return;
   g_last_completed_m5_bar = completed_bar;

   double spread_points = WR50_CurrentSpreadPoints(_Symbol);
   string comment_text = WR50_BuildShortComment(EA_SHORT_CODE, InpRunId);

   WR50Signal signal;
   WR50_ResetSignal(signal);
   if(!WR50_GetBreakoutRetestSignal(_Symbol, 1.0, 0.3, false, 0.50, 0.35, 5, 0.1,
                                    "WR50_E1R0_LONG", "WR50_E1R0_SHORT", signal))
   {
      WR50_LogBlock(EA_ID, EA_SHORT_CODE, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, EA_MAGIC,
                    "WR50_E1R0_NO_SIGNAL", signal.block_reason, spread_points, InpMaxSpreadPoints);
      return;
   }
   WR50_LogSignal(EA_ID, EA_SHORT_CODE, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, EA_MAGIC, signal, comment_text);

   string risk_reason = "";
   double current_spread = 0.0;
   double lot = WR50_NormalizeLot(_Symbol, InpFixedLot);
   if(!WR50_PassPreOrderRiskGuards(_Symbol,
                                   EA_MAGIC,
                                   signal,
                                   lot,
                                   InpMaxSpreadPoints,
                                   InpMaxTradesPerDay,
                                   InpMaxOpenPositionsForThisEA,
                                   InpMaxOpenWR50PositionsTotal,
                                   InpMaxDailyLossAccountCurrency,
                                   InpAllowSharedSymbolExposure,
                                   InpRolloverStartHour,
                                   InpRolloverStartMinute,
                                   InpRolloverEndHour,
                                   InpRolloverEndMinute,
                                   InpManualBlackoutFile,
                                   current_spread,
                                   risk_reason))
   {
      WR50_LogBlock(EA_ID, EA_SHORT_CODE, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, EA_MAGIC,
                    signal.reason_code, risk_reason, current_spread, InpMaxSpreadPoints);
      return;
   }

   MqlTradeResult result;
   string order_reason = "";
   if(!WR50_SendPendingOrder(_Symbol, EA_MAGIC, signal, lot, comment_text, InpPendingExpiryM5Bars, result, order_reason))
   {
      WR50_LogError(EA_ID, EA_SHORT_CODE, EA_VERSION, InpExperimentId, InpRunId, EA_MAGIC, "WR50_SendPendingOrder", order_reason);
      WR50_LogBlock(EA_ID, EA_SHORT_CODE, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, EA_MAGIC,
                    signal.reason_code, order_reason, current_spread, InpMaxSpreadPoints);
      return;
   }
   WR50_LogOrder(EA_ID, EA_SHORT_CODE, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, EA_MAGIC,
                 signal, lot, result.order, result.deal, result.retcode, comment_text);
}
