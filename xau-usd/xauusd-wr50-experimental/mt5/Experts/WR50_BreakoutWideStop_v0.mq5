#property strict
#property version   "1.00"
#property description "WR50 demo-only experimental breakout-retest wide-stop lane. Non-canonical, no live authorization."

#include <WR50/WR50_Common.mqh>

input bool   InpExperimentalDemoOnly = true;
input bool   InpAllowDemoTrading = false;
input string InpOwnerAuthorizationToken = "";
input string InpRequiredOwnerAuthorizationToken = "";
input string InpExperimentId = "WR50_20260609_WIDESTOP";
input string InpRunId = "R260609W";
input string InpEaId = "wr50_wst12";
input string InpEaShortCode = "WST12";
input int    InpMagicNumber = WR50_WST12_ACTIVE_MAGIC;
input int    InpMagicStart = WR50_WST12_MAGIC_START;
input int    InpMagicEnd = WR50_WST12_MAGIC_END;
input string InpAllowedSymbol = "XAUUSD";
input bool   InpAllowSymbolSuffix = true;
input double InpFixedLot = 0.01;
input int    InpMaxSpreadPoints = 75;
input double InpMaxCostR = 0.15;
input int    InpMaxTradesPerDay = 5;
input int    InpMaxOpenPositionsForThisEA = 1;
input int    InpMaxOpenWR50PositionsTotal = 5;
input double InpMaxDailyLossAccountCurrency = 100.0;
input bool   InpAllowNettingAccountForDemoExperiment = false;
input bool   InpAllowSharedSymbolExposure = false;
input bool   InpRequireDemoServerName = true;
input bool   InpRequireRuntimeRegistryFile = true;
input string InpRuntimeRegistryFile = "WR50\\wr50_runtime_registry.csv";
input bool   InpRequireAccountAllowlist = true;
input string InpAccountAllowlistFile = "WR50\\wr50_account_allowlist.csv";
input double InpTargetR = 1.20;
input int    InpMinStopDistancePoints = 375;
input double InpStopAtrMultiple = 1.20;
input double InpBreakAtrMultiple = 0.30;
input int    InpRetestProximityPoints = 5;
input double InpReferenceSlAtrMultiple = 0.10;
input int    InpRolloverStartHour = 22;
input int    InpRolloverStartMinute = 0;
input int    InpRolloverEndHour = 23;
input int    InpRolloverEndMinute = 15;
input string InpManualBlackoutFile = "WR50\\wr50_blackout_windows.csv";
input int    InpPendingExpiryM5Bars = 5;

const string EA_NAME = "WR50_BreakoutWideStop_v0";
const string EA_VERSION = "v0";
const string STRATEGY_FAMILY = "breakout_retest_wr50_experimental";
datetime g_last_completed_m5_bar = 0;

bool WR50_ApplyWideStop(WR50Signal &signal,
                        const double target_r,
                        const int min_stop_distance_points,
                        const double stop_atr_multiple,
                        double &stop_distance_points,
                        string &reason)
{
   if(!signal.has_signal)
   {
      reason = "no_signal";
      return false;
   }
   if(target_r <= 0.0)
   {
      reason = "target_r_invalid";
      return false;
   }
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point <= 0.0)
   {
      reason = "invalid_symbol_point";
      return false;
   }

   double current_stop_points = WR50_StopDistancePoints(_Symbol, signal);
   double atr_floor_points = signal.atr_points * stop_atr_multiple;
   stop_distance_points = MathMax(current_stop_points, MathMax((double)min_stop_distance_points, atr_floor_points));
   if(stop_distance_points <= 0.0)
   {
      reason = "wide_stop_distance_invalid";
      return false;
   }

   double stop_distance_price = stop_distance_points * point;
   if(signal.direction == WR50_DIRECTION_LONG)
   {
      signal.sl_price = NormalizeDouble(signal.entry_price - stop_distance_price, _Digits);
      signal.tp_price = NormalizeDouble(signal.entry_price + (stop_distance_price * target_r), _Digits);
   }
   else if(signal.direction == WR50_DIRECTION_SHORT)
   {
      signal.sl_price = NormalizeDouble(signal.entry_price + stop_distance_price, _Digits);
      signal.tp_price = NormalizeDouble(signal.entry_price - (stop_distance_price * target_r), _Digits);
   }
   else
   {
      reason = "signal_direction_invalid";
      return false;
   }
   reason = "wide_stop_applied";
   return true;
}

int OnInit()
{
   string reason = "";
   WR50_LogStartup(InpEaId, InpEaShortCode, EA_VERSION, InpExperimentId, InpRunId, InpMagicNumber, "INIT_START", "demo_only_non_canonical_wide_stop");
   if(!WR50_ValidateAccountGuard(InpExperimentalDemoOnly,
                                 InpAllowDemoTrading,
                                 InpOwnerAuthorizationToken,
                                 InpRequiredOwnerAuthorizationToken,
                                 InpEaId,
                                 EA_NAME,
                                 InpMagicNumber,
                                 InpMagicStart,
                                 InpMagicEnd,
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
      WR50_LogStartup(InpEaId, InpEaShortCode, EA_VERSION, InpExperimentId, InpRunId, InpMagicNumber, "INIT_FAILED", reason);
      Comment("WR50 WST INIT FAILED: ", reason);
      return INIT_FAILED;
   }
   WR50_LogStartup(InpEaId, InpEaShortCode, EA_VERSION, InpExperimentId, InpRunId, InpMagicNumber, "INIT_OK", reason);
   Comment("WR50 ", InpEaShortCode, " demo wide-stop experiment armed. Non-canonical.");
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
   string comment_text = WR50_BuildShortComment(InpEaShortCode, InpRunId);

   WR50Signal signal;
   WR50_ResetSignal(signal);
   string long_reason = "WR50_" + InpEaShortCode + "_LONG";
   string short_reason = "WR50_" + InpEaShortCode + "_SHORT";
   if(!WR50_GetBreakoutRetestSignal(_Symbol, 1.5, InpBreakAtrMultiple, false, 0.50, 0.35,
                                    InpRetestProximityPoints, InpReferenceSlAtrMultiple,
                                    long_reason, short_reason, signal))
   {
      WR50_LogBlock(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                    "WR50_WIDESTOP_NO_SIGNAL", signal.block_reason, spread_points, InpMaxSpreadPoints);
      return;
   }

   double stop_distance_points = 0.0;
   string stop_reason = "";
   if(!WR50_ApplyWideStop(signal, InpTargetR, InpMinStopDistancePoints, InpStopAtrMultiple, stop_distance_points, stop_reason))
   {
      WR50_LogBlock(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                    signal.reason_code, stop_reason, spread_points, InpMaxSpreadPoints);
      WR50_LogImprovementOrder(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                               signal, 0.0, InpTargetR, stop_distance_points, spread_points, 0.0, 0, 0, 0,
                               comment_text, "GUARD_BLOCK", stop_reason);
      return;
   }

   WR50_LogSignal(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber, signal, comment_text);

   string risk_reason = "";
   double current_spread = 0.0;
   double lot = WR50_NormalizeLot(_Symbol, InpFixedLot);
   if(lot > 0.01)
   {
      risk_reason = "fixed_lot_exceeds_demo_cap";
      WR50_LogBlock(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                    signal.reason_code, risk_reason, spread_points, InpMaxSpreadPoints);
      WR50_LogImprovementOrder(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                               signal, lot, InpTargetR, stop_distance_points, spread_points, 0.0, 0, 0, 0,
                               comment_text, "GUARD_BLOCK", risk_reason);
      return;
   }
   if(!WR50_PassPreOrderRiskGuards(_Symbol,
                                   InpMagicNumber,
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
      double estimated_cost_r = WR50_EstimatedCostR(_Symbol, signal, current_spread);
      WR50_LogBlock(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                    signal.reason_code, risk_reason, current_spread, InpMaxSpreadPoints);
      WR50_LogImprovementOrder(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                               signal, lot, InpTargetR, stop_distance_points, current_spread, estimated_cost_r, 0, 0, 0,
                               comment_text, "GUARD_BLOCK", risk_reason);
      return;
   }

   double estimated_cost_r = 0.0;
   string cost_reason = "";
   if(!WR50_CostRAllowed(_Symbol, signal, current_spread, InpMaxCostR, estimated_cost_r, cost_reason))
   {
      WR50_LogBlock(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                    signal.reason_code, cost_reason, current_spread, InpMaxSpreadPoints);
      WR50_LogImprovementOrder(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                               signal, lot, InpTargetR, stop_distance_points, current_spread, estimated_cost_r, 0, 0, 0,
                               comment_text, "GUARD_BLOCK", cost_reason);
      return;
   }

   MqlTradeResult result;
   string order_reason = "";
   if(!WR50_SendPendingOrder(_Symbol, InpMagicNumber, signal, lot, comment_text, InpPendingExpiryM5Bars, result, order_reason))
   {
      WR50_LogError(InpEaId, InpEaShortCode, EA_VERSION, InpExperimentId, InpRunId, InpMagicNumber, "WR50_SendPendingOrder", order_reason);
      WR50_LogBlock(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                    signal.reason_code, order_reason, current_spread, InpMaxSpreadPoints);
      WR50_LogImprovementOrder(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                               signal, lot, InpTargetR, stop_distance_points, current_spread, estimated_cost_r, 0, 0, result.retcode,
                               comment_text, "ORDER_SEND_FAILED", order_reason);
      return;
   }
   WR50_LogOrder(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                 signal, lot, result.order, result.deal, result.retcode, comment_text);
   WR50_LogImprovementOrder(InpEaId, InpEaShortCode, EA_VERSION, STRATEGY_FAMILY, InpExperimentId, InpRunId, InpMagicNumber,
                            signal, lot, InpTargetR, stop_distance_points, current_spread, estimated_cost_r,
                            result.order, result.deal, result.retcode, comment_text, "ORDER_SEND_OK", "pass");
}
