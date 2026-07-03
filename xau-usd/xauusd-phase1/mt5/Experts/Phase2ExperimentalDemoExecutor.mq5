// NON_CANONICAL / EXPERIMENTAL DEMO ONLY / DO NOT DEPLOY AS PHASE2.
// This file contains guarded demo broker-action logic for a quarantined owner-requested
// experiment. It is not part of the canonical Phase 1 dry-run shell, cannot authorize
// Phase 2, and must remain excluded from canonical deploy/compile bundles.
#property strict
#property version   "1.000"
#property description "Experimental demo executor attachment. Demo account only; sends small guarded orders."

#include <Phase1/Phase1Types.mqh>
#include <Phase1/Phase1BreakoutRetest.mqh>
#include <DirectionStateShadow.mqh>
#include <A3MlShadowTap.mqh>

input string InpRunId = "phase2-experimental-demo-executor-v0.2";
input bool InpDryRunOnly = false;
input bool InpBrokerActionAllowed = false;
input string InpCandidate = "breakout_retest";
input string InpCandidateStatus = "EXPERIMENTAL_QUARANTINE_REVIEW_ONLY";
input string InpFamilyLifecycleStatus = "COST_SUSPENDED_CANONICAL";
input string InpTargetSymbol = "XAUUSD";
input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,GBPUSD,BTCUSD";
input string InpExpectedServerMarker = "Demo";
input string InpAllowedAccountLoginsCsv = "";
input string InpExperimentalAuthorizationToken = "";
input string InpRequiredExperimentalAuthorizationToken = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY";
input string InpCostSuspensionAcknowledgementToken = "";
input string InpRequiredCostSuspensionAcknowledgementToken = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT";
input string InpAuthorizedCandidatesCsv = "breakout_retest";
input string InpAttachmentLogFileName = "experimental_demo_executor_signal_log_v02.csv";
input string InpStartupLogFileName = "experimental_demo_executor_startup_v02.csv";
input string InpOrderLogFileName = "experimental_demo_executor_order_log_v02.csv";
input string InpManagementLogFileName = "experimental_demo_executor_management_log_v02.csv";
input string InpDirectionStateFileName = "dirstate_xauusd.csv";
input string InpKillSwitchFileName = "experimental_demo_kill_switch.txt";
input double InpFixedLot = 0.01;
input double InpEURUSDFixedLot = 0.01;
input double InpGBPUSDFixedLot = 0.01;
input int InpMaxOrdersPerDay = 0;
input int InpMaxAccountOrdersPerDay = 0;
input int InpMinSecondsBetweenOrders = 0;
input int InpMaxOpenPositionsPerInstance = 0;
input int InpMaxOpenPositionsPerMagic = 1;
input int InpDeviationPoints = 50;
input double InpMaxEstimatedCostR = 0.00;
input double InpMaxMeasuredSpreadPoints = 0.0;
input bool InpTradeSessionGateEnabled = false;
input int InpTradeSessionStartHour = 0;
input int InpTradeSessionEndHour = 23;
input bool InpSmartTrendFilterEnabled = false;
input bool InpSmartTrendFilterShadowOnly = true;
input int InpSmartTrendD1LagBars = 5;
input int InpSmartTrendH1LagBars = 3;
input bool InpSmartTrendRequireD1 = true;
input bool InpSmartTrendRequireH1 = true;
input double InpSmartTrendMinD1Aligned = 0.25;
input double InpSmartTrendMinH1Aligned = 0.35;
input bool InpFastStopoutFilterEnabled = false;
input bool InpFastStopoutFilterShadowOnly = true;
input double InpFastStopoutMinStopPoints = 0.0;
input double InpFastStopoutMinConfirmationBodyRange = 0.0;
input double InpFastStopoutMinCloseLocation = 0.0;
input bool InpProfitProtectionEnabled = false;
input bool InpProfitProtectionShadowOnly = true;
input double InpProfitProtectionTriggerR = 1.25;
input double InpProfitProtectionLockR = 0.80;
input string InpDirectionMode = "BOTH"; // BOTH, LONG_ONLY, SHORT_ONLY

CPhase1BreakoutRetestObserver g_breakout_observer;
datetime g_last_m5_bar_time = 0;
datetime g_last_order_submit_time = 0;
string g_order_day_key = "";
int g_orders_today = 0;
string g_family_mutex_claim_name = "";
datetime g_family_mutex_claim_bar_time = 0;

string BoolText(const bool value)
{
   return value ? "true" : "false";
}

string LowerText(string value)
{
   StringToLower(value);
   return value;
}

bool ContainsText(const string haystack, const string needle)
{
   return StringFind(LowerText(haystack), LowerText(needle)) >= 0;
}

string TrimToken(string value)
{
   StringTrimLeft(value);
   StringTrimRight(value);
   return value;
}

bool CsvContainsSymbol(const string csv, const string symbol_name)
{
   string tokens[];
   int count = StringSplit(csv, ',', tokens);
   for(int index = 0; index < count; index++)
   {
      if(TrimToken(tokens[index]) == symbol_name)
         return true;
   }
   return false;
}

bool CsvContainsTextToken(const string csv, const string wanted)
{
   string tokens[];
   int count = StringSplit(csv, ',', tokens);
   string wanted_trimmed = TrimToken(wanted);
   for(int index = 0; index < count; index++)
   {
      if(TrimToken(tokens[index]) == wanted_trimmed)
         return true;
   }
   return false;
}

bool DirectionModeAllows(const string direction_text)
{
   string mode = InpDirectionMode;
   StringToUpper(mode);
   int direction = SignalDirectionSign(direction_text);
   if(mode == "" || mode == "BOTH" || mode == "ALL")
      return true;
   if((mode == "LONG_ONLY" || mode == "BUY_ONLY" || mode == "LONG") && direction > 0)
      return true;
   if((mode == "SHORT_ONLY" || mode == "SELL_ONLY" || mode == "SHORT") && direction < 0)
      return true;
   return false;
}

bool AccountLoginWhitelisted()
{
   return CsvContainsTextToken(InpAllowedAccountLoginsCsv, IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)));
}

bool CandidateExecutionAuthorized()
{
   return CsvContainsTextToken(InpAuthorizedCandidatesCsv, InpCandidate);
}

bool ExperimentalAuthorizationTokenValid()
{
   return TrimToken(InpExperimentalAuthorizationToken) == TrimToken(InpRequiredExperimentalAuthorizationToken);
}

bool FamilyLifecycleCostSuspended()
{
   return ContainsText(InpFamilyLifecycleStatus, "cost_suspended");
}

bool CostSuspensionAcknowledgementTokenValid()
{
   if(!FamilyLifecycleCostSuspended())
      return true;
   return TrimToken(InpCostSuspensionAcknowledgementToken) == TrimToken(InpRequiredCostSuspensionAcknowledgementToken);
}

double CurrentSpreadPoints()
{
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point <= 0.0)
      return 0.0;
   return (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / point;
}

double EstimatedCostRForObservation(const Phase1BreakoutRetestObservation &observation, const double spread_points)
{
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double risk_price = MathAbs(observation.entry_price - observation.stop_loss);
   if(point <= 0.0 || risk_price <= 0.0)
      return 0.0;
   return spread_points * point / risk_price;
}

int SignalDirectionSign(const string direction_text)
{
   if(direction_text == "LONG" || direction_text == "BUY")
      return 1;
   if(direction_text == "SHORT" || direction_text == "SELL")
      return -1;
   return 0;
}

bool CopyIndicatorValue(const int handle, const int shift, double &value)
{
   if(handle == INVALID_HANDLE)
      return false;
   double buffer[];
   ArraySetAsSeries(buffer, true);
   int copied = CopyBuffer(handle, 0, shift, 1, buffer);
   if(copied != 1)
      return false;
   value = buffer[0];
   return value != EMPTY_VALUE && MathIsValidNumber(value);
}

bool Ema20Value(const ENUM_TIMEFRAMES timeframe, const int shift, double &value)
{
   int handle = iMA(_Symbol, timeframe, 20, 0, MODE_EMA, PRICE_CLOSE);
   bool ok = CopyIndicatorValue(handle, shift, value);
   if(handle != INVALID_HANDLE)
      IndicatorRelease(handle);
   return ok;
}

bool Atr14Value(const ENUM_TIMEFRAMES timeframe, const int shift, double &value)
{
   int handle = iATR(_Symbol, timeframe, 14);
   bool ok = CopyIndicatorValue(handle, shift, value);
   if(handle != INVALID_HANDLE)
      IndicatorRelease(handle);
   return ok && value > 0.0;
}

bool AlignedEmaSlopeAtr(
   const ENUM_TIMEFRAMES timeframe,
   const int lag_bars,
   const int direction_sign,
   double &score
)
{
   score = 0.0;
   if(lag_bars < 1 || direction_sign == 0)
      return false;
   if(Bars(_Symbol, timeframe) <= lag_bars + 20)
      return false;

   double current_ema = 0.0;
   double previous_ema = 0.0;
   double atr = 0.0;
   if(!Ema20Value(timeframe, 1, current_ema))
      return false;
   if(!Ema20Value(timeframe, 1 + lag_bars, previous_ema))
      return false;
   if(!Atr14Value(timeframe, 1, atr))
      return false;

   score = direction_sign * (current_ema - previous_ema) / atr;
   return MathIsValidNumber(score);
}

bool SmartTrendFilterPass(const Phase1BreakoutRetestObservation &observation, string &guard_reason)
{
   if(!InpSmartTrendFilterEnabled)
      return true;
   int direction_sign = SignalDirectionSign(observation.direction_text);
   if(direction_sign == 0)
   {
      guard_reason = "SMART_TREND_NO_DIRECTION";
      return false;
   }

   double d1_score = 0.0;
   double h1_score = 0.0;
   bool d1_available = AlignedEmaSlopeAtr(PERIOD_D1, InpSmartTrendD1LagBars, direction_sign, d1_score);
   bool h1_available = AlignedEmaSlopeAtr(PERIOD_H1, InpSmartTrendH1LagBars, direction_sign, h1_score);
   string d1_text = d1_available ? DoubleToString(d1_score, 4) : "NA";
   string h1_text = h1_available ? DoubleToString(h1_score, 4) : "NA";

   if(InpSmartTrendRequireD1 && !d1_available)
   {
      guard_reason = "SMART_TREND_D1_UNAVAILABLE";
      return false;
   }
   if(InpSmartTrendRequireH1 && !h1_available)
   {
      guard_reason = "SMART_TREND_H1_UNAVAILABLE";
      return false;
   }
   if(InpSmartTrendRequireD1 && d1_score < InpSmartTrendMinD1Aligned)
   {
      guard_reason = "SMART_TREND_D1_BLOCK_d1=" + DoubleToString(d1_score, 4) + "_min=" + DoubleToString(InpSmartTrendMinD1Aligned, 4);
      return false;
   }
   if(InpSmartTrendRequireH1 && h1_score < InpSmartTrendMinH1Aligned)
   {
      guard_reason = "SMART_TREND_H1_BLOCK_h1=" + DoubleToString(h1_score, 4) + "_min=" + DoubleToString(InpSmartTrendMinH1Aligned, 4);
      return false;
   }
   guard_reason = "SMART_TREND_PASS_d1=" + d1_text + "_h1=" + h1_text + "_require_d1=" + BoolText(InpSmartTrendRequireD1) + "_require_h1=" + BoolText(InpSmartTrendRequireH1);
   return true;
}

bool FastStopoutFilterPass(const Phase1BreakoutRetestObservation &observation, string &guard_reason)
{
   if(!InpFastStopoutFilterEnabled)
      return true;

   if(InpFastStopoutMinStopPoints > 0.0 && observation.stop_distance_points < InpFastStopoutMinStopPoints)
   {
      guard_reason = "FAST_STOPOUT_MIN_STOP_BLOCK_stop="
         + DoubleToString(observation.stop_distance_points, 2)
         + "_min=" + DoubleToString(InpFastStopoutMinStopPoints, 2);
      return false;
   }

   int shift = observation.confirmation_shift;
   if(shift < 1)
      shift = 1;
   double open_price = iOpen(_Symbol, PERIOD_M5, shift);
   double high_price = iHigh(_Symbol, PERIOD_M5, shift);
   double low_price = iLow(_Symbol, PERIOD_M5, shift);
   double close_price = iClose(_Symbol, PERIOD_M5, shift);
   if(open_price <= 0.0 || high_price <= 0.0 || low_price <= 0.0 || close_price <= 0.0 || high_price <= low_price)
   {
      guard_reason = "FAST_STOPOUT_CONFIRMATION_CONTEXT_UNAVAILABLE";
      return false;
   }

   double range = high_price - low_price;
   double body_ratio = range > 0.0 ? MathAbs(close_price - open_price) / range : 0.0;
   double close_location = range > 0.0 ? (close_price - low_price) / range : 0.5;

   if(InpFastStopoutMinConfirmationBodyRange > 0.0 && body_ratio < InpFastStopoutMinConfirmationBodyRange)
   {
      guard_reason = "FAST_STOPOUT_BODY_BLOCK_body="
         + DoubleToString(body_ratio, 4)
         + "_min=" + DoubleToString(InpFastStopoutMinConfirmationBodyRange, 4);
      return false;
   }

   if(InpFastStopoutMinCloseLocation > 0.0)
   {
      int direction = SignalDirectionSign(observation.direction_text);
      if(direction > 0 && close_location < InpFastStopoutMinCloseLocation)
      {
         guard_reason = "FAST_STOPOUT_LONG_CLOSE_LOCATION_BLOCK_loc="
            + DoubleToString(close_location, 4)
            + "_min=" + DoubleToString(InpFastStopoutMinCloseLocation, 4);
         return false;
      }
      if(direction < 0 && close_location > 1.0 - InpFastStopoutMinCloseLocation)
      {
         guard_reason = "FAST_STOPOUT_SHORT_CLOSE_LOCATION_BLOCK_loc="
            + DoubleToString(close_location, 4)
            + "_max=" + DoubleToString(1.0 - InpFastStopoutMinCloseLocation, 4);
         return false;
      }
   }

   guard_reason = "FAST_STOPOUT_PASS_stop="
      + DoubleToString(observation.stop_distance_points, 2)
      + "_body=" + DoubleToString(body_ratio, 4)
      + "_close_loc=" + DoubleToString(close_location, 4);
   return true;
}

bool IsAllowedCandidate(const string candidate)
{
   return candidate == "breakout_retest"
      || candidate == "swing_breakout_retest_v0"
      || candidate == "symbol_normalized_round_retest_v0"
      || candidate == "round_number_retest_v0"
      || candidate == "session_extreme_retest_v0";
}

bool CandidateHasNativeObserver(const string candidate)
{
   return IsAllowedCandidate(candidate);
}

bool CandidateUsesSwingObserver(const string candidate)
{
   return candidate == "swing_breakout_retest_v0";
}

bool CandidateUsesSymbolNormalizedRoundObserver(const string candidate)
{
   return candidate == "symbol_normalized_round_retest_v0";
}

bool CandidateUsesRoundObserver(const string candidate)
{
   return candidate == "round_number_retest_v0" || CandidateUsesSymbolNormalizedRoundObserver(candidate);
}

bool CandidateUsesSessionExtremeObserver(const string candidate)
{
   return candidate == "session_extreme_retest_v0";
}

struct DemoRetestCandidate
{
   bool valid;
   string level_kind;
   double level_price;
   double entry_price;
   double stop_loss;
   double take_profit;
   double stop_distance_points;
   int break_shift;
};

void ResetDemoCandidate(DemoRetestCandidate &candidate)
{
   candidate.valid = false;
   candidate.level_kind = "none";
   candidate.level_price = 0.0;
   candidate.entry_price = 0.0;
   candidate.stop_loss = 0.0;
   candidate.take_profit = 0.0;
   candidate.stop_distance_points = 0.0;
   candidate.break_shift = -1;
}

double AverageRangePrice(const string symbol_name, const ENUM_TIMEFRAMES timeframe, const int periods, const int start_shift)
{
   double total = 0.0;
   int counted = 0;
   for(int shift = start_shift; shift < start_shift + periods; shift++)
   {
      double high_price = iHigh(symbol_name, timeframe, shift);
      double low_price = iLow(symbol_name, timeframe, shift);
      if(high_price <= 0.0 || low_price <= 0.0 || high_price < low_price)
         continue;
      total += high_price - low_price;
      counted++;
   }
   if(counted <= 0)
      return 0.0;
   return total / counted;
}

bool DemoBreakValid(const double break_close, const double break_atr, const double level_price, const bool is_long)
{
   if(is_long)
      return break_close >= level_price + 0.30 * break_atr;
   return break_close <= level_price - 0.30 * break_atr;
}

bool DemoRetestValid(
   const double retest_high,
   const double retest_low,
   const double retest_close,
   const double level_price,
   const double point,
   const bool is_long
)
{
   if(is_long)
      return retest_low <= level_price + 5.0 * point && retest_close >= level_price;
   return retest_high >= level_price - 5.0 * point && retest_close <= level_price;
}

void BuildDemoPlan(
   const double retest_high,
   const double retest_low,
   const double retest_atr,
   const double point,
   const bool is_long,
   DemoRetestCandidate &candidate
)
{
   if(is_long)
   {
      candidate.entry_price = retest_high + point;
      candidate.stop_loss = retest_low - 0.10 * retest_atr;
      double risk_price = candidate.entry_price - candidate.stop_loss;
      candidate.take_profit = candidate.entry_price + 1.50 * risk_price;
      candidate.stop_distance_points = risk_price / point;
   }
   else
   {
      candidate.entry_price = retest_low - point;
      candidate.stop_loss = retest_high + 0.10 * retest_atr;
      double risk_price = candidate.stop_loss - candidate.entry_price;
      candidate.take_profit = candidate.entry_price - 1.50 * risk_price;
      candidate.stop_distance_points = risk_price / point;
   }
}

void AddDemoCandidate(
   DemoRetestCandidate &levels[],
   int &count,
   const string level_kind,
   const double level_price,
   const double point
)
{
   if(level_price <= 0.0 || point <= 0.0 || count >= ArraySize(levels))
      return;
   for(int index = 0; index < count; index++)
   {
      if(MathAbs(levels[index].level_price - level_price) <= 10.0 * point)
         return;
   }
   ResetDemoCandidate(levels[count]);
   levels[count].valid = true;
   levels[count].level_kind = level_kind;
   levels[count].level_price = level_price;
   count++;
}

void RoundIncrements(const bool symbol_normalized, const double point, double &a, double &b, double &c)
{
   if(symbol_normalized && point <= 0.0001)
   {
      a = 0.0050;
      b = 0.0100;
      c = 0.0250;
      return;
   }
   if(symbol_normalized && point < 0.005)
   {
      a = 0.50;
      b = 1.00;
      c = 2.50;
      return;
   }
   a = 10.0;
   b = 25.0;
   c = 50.0;
}

void AddRoundLevels(
   const string symbol_name,
   const double point,
   const double break_close,
   const bool is_long,
   const bool symbol_normalized,
   DemoRetestCandidate &levels[],
   int &count
)
{
   double increments[3];
   RoundIncrements(symbol_normalized, point, increments[0], increments[1], increments[2]);
   int digits = (int)SymbolInfoInteger(symbol_name, SYMBOL_DIGITS);
   for(int index = 0; index < 3; index++)
   {
      double increment = increments[index];
      if(increment <= 0.0)
         continue;
      double level_price = is_long ? MathFloor(break_close / increment) * increment : MathCeil(break_close / increment) * increment;
      level_price = NormalizeDouble(level_price, digits);
      if(is_long && (level_price <= 0.0 || level_price >= break_close))
         continue;
      if(!is_long && level_price <= break_close)
         continue;
      string prefix = symbol_normalized ? "symbol_round_" : "round_number_";
      AddDemoCandidate(levels, count, prefix + DoubleToString(increment, 5), level_price, point);
   }
}

int MinuteOfDay(const datetime value)
{
   MqlDateTime parts;
   TimeToStruct(value, parts);
   return parts.hour * 60 + parts.min;
}

double SessionExtremeLevel(
   const string symbol_name,
   const datetime day_start,
   const int start_minute,
   const int end_minute,
   const bool is_high
)
{
   datetime start_time = day_start + start_minute * 60;
   datetime end_time = day_start + end_minute * 60;
   double value = 0.0;
   for(int shift = 3; shift < 400; shift++)
   {
      datetime bar_time = iTime(symbol_name, PERIOD_M5, shift);
      if(bar_time <= 0)
         continue;
      if(bar_time < start_time || bar_time >= end_time)
         continue;
      double price = is_high ? iHigh(symbol_name, PERIOD_M5, shift) : iLow(symbol_name, PERIOD_M5, shift);
      if(price <= 0.0)
         continue;
      if(value <= 0.0)
         value = price;
      else if(is_high && price > value)
         value = price;
      else if(!is_high && price < value)
         value = price;
   }
   return value;
}

void AddSessionExtremeLevels(
   const string symbol_name,
   const double point,
   const datetime break_time,
   const bool is_long,
   DemoRetestCandidate &levels[],
   int &count
)
{
   int start_minute = MinuteOfDay(break_time);
   datetime day_start = StringToTime(TimeToString(break_time, TIME_DATE));
   if(start_minute >= 7 * 60)
   {
      double asia_level = SessionExtremeLevel(symbol_name, day_start, 0, 6 * 60, is_long);
      AddDemoCandidate(levels, count, is_long ? "asia_high" : "asia_low", asia_level, point);
   }
   if(start_minute >= 13 * 60 + 30)
   {
      double london_level = SessionExtremeLevel(symbol_name, day_start, 7 * 60, 11 * 60, is_long);
      AddDemoCandidate(levels, count, is_long ? "london_high" : "london_low", london_level, point);
   }
}

int DemoCandidateLevels(
   const string candidate,
   const string symbol_name,
   const double point,
   const double break_close,
   const datetime break_time,
   const bool is_long,
   DemoRetestCandidate &levels[]
)
{
   int count = 0;
   if(CandidateUsesRoundObserver(candidate))
      AddRoundLevels(symbol_name, point, break_close, is_long, CandidateUsesSymbolNormalizedRoundObserver(candidate), levels, count);
   else if(CandidateUsesSessionExtremeObserver(candidate))
      AddSessionExtremeLevels(symbol_name, point, break_time, is_long, levels, count);
   return count;
}

string CandidateReasonPrefix(const string candidate)
{
   if(candidate == "symbol_normalized_round_retest_v0")
      return "SYMBOL_NORMALIZED_ROUND_RETEST";
   if(candidate == "round_number_retest_v0")
      return "ROUND_NUMBER_RETEST";
   if(candidate == "session_extreme_retest_v0")
      return "SESSION_EXTREME_RETEST";
   return "EXPERIMENTAL_RETEST";
}

bool EvaluateExperimentalRetestObserver(
   const string candidate,
   const string symbol_name,
   const double point,
   Phase1BreakoutRetestObservation &observation
)
{
   Phase1ResetBreakoutRetestObservation(observation);
   if(point <= 0.0)
   {
      observation.stage = "NO_POINT";
      observation.reason_code = "point_unavailable";
      return false;
   }
   if(Bars(symbol_name, PERIOD_M5) < 80)
   {
      observation.stage = "INSUFFICIENT_BARS";
      observation.reason_code = "insufficient_m5_history";
      return false;
   }

   double confirmation_open = iOpen(symbol_name, PERIOD_M5, 1);
   double confirmation_close = iClose(symbol_name, PERIOD_M5, 1);
   if(confirmation_open <= 0.0 || confirmation_close <= 0.0)
   {
      observation.stage = "NO_CONFIRMATION_BAR";
      observation.reason_code = "confirmation_bar_unavailable";
      return false;
   }

   bool is_long = false;
   if(confirmation_close > confirmation_open)
      is_long = true;
   else if(confirmation_close < confirmation_open)
      is_long = false;
   else
   {
      observation.stage = "WAIT_CONFIRMATION";
      observation.reason_code = "confirmation_candle_neutral";
      return false;
   }

   observation.direction_text = is_long ? "LONG" : "SHORT";
   observation.confirmation_valid = true;
   observation.confirmation_shift = 1;
   observation.retest_shift = 2;
   observation.stage = "CONFIRMATION_DETECTED";

   double retest_high = iHigh(symbol_name, PERIOD_M5, 2);
   double retest_low = iLow(symbol_name, PERIOD_M5, 2);
   double retest_close = iClose(symbol_name, PERIOD_M5, 2);
   double retest_atr = AverageRangePrice(symbol_name, PERIOD_M5, 14, 2);
   if(retest_high <= 0.0 || retest_low <= 0.0 || retest_close <= 0.0 || retest_atr <= 0.0)
   {
      observation.stage = "WAIT_RETEST";
      observation.reason_code = "retest_context_unavailable";
      return false;
   }

   DemoRetestCandidate best;
   ResetDemoCandidate(best);
   for(int shift = 3; shift <= 22; shift++)
   {
      double break_atr = AverageRangePrice(symbol_name, PERIOD_M5, 14, shift);
      double break_close = iClose(symbol_name, PERIOD_M5, shift);
      datetime break_time = iTime(symbol_name, PERIOD_M5, shift);
      if(break_atr <= 0.0 || break_close <= 0.0 || break_time <= 0)
         continue;

      DemoRetestCandidate levels[3];
      for(int init = 0; init < 3; init++)
         ResetDemoCandidate(levels[init]);
      int level_count = DemoCandidateLevels(candidate, symbol_name, point, break_close, break_time, is_long, levels);
      for(int index = 0; index < level_count; index++)
      {
         DemoRetestCandidate row = levels[index];
         row.break_shift = shift;
         if(!DemoBreakValid(break_close, break_atr, row.level_price, is_long))
            continue;
         if(!DemoRetestValid(retest_high, retest_low, retest_close, row.level_price, point, is_long))
            continue;
         BuildDemoPlan(retest_high, retest_low, retest_atr, point, is_long, row);
         if(row.stop_distance_points <= 0.0)
            continue;
         if(!best.valid || row.stop_distance_points < best.stop_distance_points)
            best = row;
      }
   }

   observation.level_found = best.valid;
   if(!best.valid)
   {
      observation.stage = "WAIT_LEVEL_BREAK_RETEST";
      string direction = is_long ? "long" : "short";
      observation.reason_code = "no_" + direction + "_" + candidate + "_candidate";
      return false;
   }

   observation.break_found = true;
   observation.retest_valid = true;
   observation.stage = "WOULD_SIGNAL";
   observation.reason_code = CandidateReasonPrefix(candidate) + (is_long ? "_LONG_DRY_RUN" : "_SHORT_DRY_RUN");
   observation.would_signal = true;
   observation.level_kind = best.level_kind;
   observation.level_price = best.level_price;
   observation.entry_price = best.entry_price;
   observation.stop_loss = best.stop_loss;
   observation.take_profit = best.take_profit;
   observation.stop_distance_points = best.stop_distance_points;
   observation.break_shift = best.break_shift;
   return true;
}

bool AppendCsvRow(const string file_name, const string &values[])
{
   int handle = INVALID_HANDLE;
   for(int attempt = 0; attempt < 20; attempt++)
   {
      handle = FileOpen(file_name, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
      if(handle != INVALID_HANDLE)
         break;
      Sleep(50);
   }
   if(handle == INVALID_HANDLE)
   {
      Print("Could not open ", file_name, " error=", GetLastError());
      return false;
   }
   FileSeek(handle, 0, SEEK_END);
   string line = "";
   for(int index = 0; index < ArraySize(values); index++)
   {
      if(index > 0)
         line += ",";
      line += CsvEscape(values[index]);
   }
   FileWriteString(handle, line + "\r\n");
   FileFlush(handle);
   FileClose(handle);
   return true;
}

bool KillSwitchActive()
{
   if(!FileIsExist(InpKillSwitchFileName))
      return false;
   int handle = FileOpen(InpKillSwitchFileName, FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle != INVALID_HANDLE)
      FileClose(handle);
   return true; // Presence is enough; operators should not need to type KILL during an emergency.
}

bool AccountTradeModeDemo()
{
   return AccountInfoInteger(ACCOUNT_TRADE_MODE) == ACCOUNT_TRADE_MODE_DEMO;
}

int ServerHourNow()
{
   MqlDateTime parts;
   TimeToStruct(TimeCurrent(), parts);
   return parts.hour;
}

bool ServerHourInTradeSession()
{
   if(!InpTradeSessionGateEnabled)
      return true;

   int start_hour = InpTradeSessionStartHour;
   int end_hour = InpTradeSessionEndHour;
   if(start_hour < 0)
      start_hour = 0;
   if(start_hour > 23)
      start_hour = 23;
   if(end_hour < 0)
      end_hour = 0;
   if(end_hour > 23)
      end_hour = 23;

   int hour = ServerHourNow();
   if(start_hour <= end_hour)
      return hour >= start_hour && hour <= end_hour;
   return hour >= start_hour || hour <= end_hour;
}

string CompactDateKey()
{
   string key = TimeToString(TimeCurrent(), TIME_DATE);
   StringReplace(key, ".", "");
   StringReplace(key, "-", "");
   StringReplace(key, " ", "");
   return key;
}

string AccountOrderCounterName()
{
   return "P2DEMO_ORD_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + CompactDateKey();
}

int AccountOrdersToday()
{
   string name = AccountOrderCounterName();
   if(!GlobalVariableCheck(name))
      return 0;
   return (int)GlobalVariableGet(name);
}

void IncrementAccountOrdersToday()
{
   string name = AccountOrderCounterName();
   GlobalVariableSet(name, (double)(AccountOrdersToday() + 1));
}

bool IsExperimentalMagic(const long magic)
{
   return magic >= 920000 && magic < 921000;
}

int CountOpenExposureForAccount()
{
   int count = 0;
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      if(IsExperimentalMagic((long)PositionGetInteger(POSITION_MAGIC)))
         count++;
   }
   for(int index = 0; index < OrdersTotal(); index++)
   {
      ulong ticket = OrderGetTicket(index);
      if(ticket == 0)
         continue;
      if(!OrderSelect(ticket))
         continue;
      if(IsExperimentalMagic((long)OrderGetInteger(ORDER_MAGIC)))
         count++;
   }
   return count;
}

string CsvEscape(string value)
{
   bool needs_quote = StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0;
   StringReplace(value, "\"", "\"\"");
   if(needs_quote)
      return "\"" + value + "\"";
   return value;
}

bool EnsureAttachmentLogHeader()
{
   if(FileIsExist(InpAttachmentLogFileName))
      return true;

   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "symbol",
      "candidate",
      "candidate_status",
      "family_lifecycle_status",
      "qualified_symbol",
      "dry_run",
      "broker_action_allowed",
      "observer_supported",
      "m5_bar_time",
      "bid",
      "ask",
      "spread_points",
      "stage",
      "direction",
      "would_signal",
      "reason_code",
      "level_kind",
      "level_price",
      "entry_price",
      "stop_loss",
      "take_profit",
      "stop_distance_points",
      "dirstate_direction",
      "dirstate_regime",
      "dirstate_strength"
   };
   return AppendCsvRow(InpAttachmentLogFileName, header);
}

bool EnsureStartupLogHeader()
{
   if(FileIsExist(InpStartupLogFileName))
      return true;

   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "symbol",
      "candidate",
      "candidate_status",
      "family_lifecycle_status",
      "qualified_symbols",
      "account_login",
      "allowed_account_logins",
      "authorized_candidates",
      "dry_run",
      "broker_action_allowed",
      "observer_supported",
      "authorization_token_present",
      "cost_suspension_ack_token_present",
      "account_max_orders_per_day",
      "account_max_open_positions",
      "max_estimated_cost_R",
      "max_measured_spread_points",
      "kill_switch_file",
      "startup_status"
   };
   return AppendCsvRow(InpStartupLogFileName, header);
}

bool WriteStartupRow(const string status_text)
{
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpFamilyLifecycleStatus,
      InpQualifiedSymbolsCsv,
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      InpAllowedAccountLoginsCsv,
      InpAuthorizedCandidatesCsv,
      BoolText(InpDryRunOnly),
      BoolText(InpBrokerActionAllowed),
      BoolText(CandidateHasNativeObserver(InpCandidate)),
      BoolText(StringLen(TrimToken(InpExperimentalAuthorizationToken)) > 0),
      BoolText(StringLen(TrimToken(InpCostSuspensionAcknowledgementToken)) > 0),
      IntegerToString(InpMaxAccountOrdersPerDay),
      "UNLIMITED",
      DoubleToString(InpMaxEstimatedCostR, 4),
      DoubleToString(InpMaxMeasuredSpreadPoints, 2),
      InpKillSwitchFileName,
      status_text
   };
   return AppendCsvRow(InpStartupLogFileName, row);
}

bool EnsureOrderLogHeader()
{
   if(FileIsExist(InpOrderLogFileName))
      return true;

   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "account_login",
      "symbol",
      "candidate",
      "candidate_status",
      "family_lifecycle_status",
      "candidate_family_status",
      "experimental_quarantine",
      "canonical_phase2_evidence",
      "phase2_readiness_override",
      "magic",
      "broker_action_allowed",
      "dry_run",
      "cost_suspension_ack_token_present",
      "action",
      "direction",
      "volume",
      "order_mode",
      "spread_at_signal_points",
      "spread_at_order_points",
      "signal_entry_price",
      "request_price",
      "actual_request_price",
      "sl",
      "tp",
      "retcode",
      "retcode_description",
      "order_ticket",
      "deal_ticket",
      "result_price",
      "result_volume",
      "slippage_points",
      "estimated_cost_R",
      "stop_distance_points",
      "account_orders_today",
      "account_open_exposure",
      "reason_code",
      "guard_reason",
      "dirstate_direction",
      "dirstate_regime",
      "dirstate_strength"
   };
   return AppendCsvRow(InpOrderLogFileName, header);
}

bool EnsureManagementLogHeader()
{
   if(FileIsExist(InpManagementLogFileName))
      return true;

   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "account_login",
      "symbol",
      "candidate",
      "magic",
      "action",
      "position_ticket",
      "direction",
      "volume",
      "open_price",
      "initial_sl",
      "current_sl",
      "desired_sl",
      "tp",
      "unrealized_r",
      "trigger_r",
      "lock_r",
      "shadow_only",
      "retcode",
      "retcode_description",
      "reason"
   };
   return AppendCsvRow(InpManagementLogFileName, header);
}

int CandidateMagicOffset(const string candidate)
{
   if(candidate == "breakout_retest")
      return 10;
   if(candidate == "swing_breakout_retest_v0")
      return 20;
   if(candidate == "symbol_normalized_round_retest_v0")
      return 30;
   if(candidate == "round_number_retest_v0")
      return 40;
   if(candidate == "session_extreme_retest_v0")
      return 50;
   return 90;
}

int SymbolMagicOffset(const string symbol_name)
{
   if(symbol_name == "XAUUSD")
      return 1;
   if(symbol_name == "EURUSD")
      return 2;
   if(symbol_name == "USDJPY")
      return 3;
   if(symbol_name == "GBPUSD")
      return 4;
   if(symbol_name == "BTCUSD")
      return 5;
   return 9;
}

long InstanceMagic()
{
   return 920000 + CandidateMagicOffset(InpCandidate) * 10 + SymbolMagicOffset(_Symbol);
}

string ProfitProtectionStateName(const string prefix, const ulong ticket)
{
   return prefix
      + "_"
      + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN))
      + "_"
      + IntegerToString((int)InstanceMagic())
      + "_"
      + IntegerToString((int)ticket);
}

double InitialStopForPosition(const ulong ticket, const double current_sl)
{
   string name = ProfitProtectionStateName("P2EXP_INITIAL_SL", ticket);
   if(GlobalVariableCheck(name))
      return GlobalVariableGet(name);
   if(current_sl > 0.0)
      GlobalVariableSet(name, current_sl);
   return current_sl;
}

double PositionRiskPrice(const ENUM_POSITION_TYPE type, const double open_price, const double initial_sl)
{
   if(initial_sl <= 0.0)
      return 0.0;
   if(type == POSITION_TYPE_BUY && initial_sl >= open_price)
      return 0.0;
   if(type == POSITION_TYPE_SELL && initial_sl <= open_price)
      return 0.0;
   return MathAbs(open_price - initial_sl);
}

double PositionUnrealizedR(
   const ENUM_POSITION_TYPE type,
   const double open_price,
   const double risk_price,
   const double bid,
   const double ask
)
{
   if(risk_price <= 0.0)
      return 0.0;
   if(type == POSITION_TYPE_BUY)
      return (bid - open_price) / risk_price;
   if(type == POSITION_TYPE_SELL)
      return (open_price - ask) / risk_price;
   return 0.0;
}

bool StopImprovesOnly(const ENUM_POSITION_TYPE type, const double current_sl, const double desired_sl)
{
   if(desired_sl <= 0.0)
      return false;
   if(type == POSITION_TYPE_BUY)
      return current_sl <= 0.0 || desired_sl > current_sl;
   if(type == POSITION_TYPE_SELL)
      return current_sl <= 0.0 || desired_sl < current_sl;
   return false;
}

bool StopRespectsBrokerDistance(const ENUM_POSITION_TYPE type, const string symbol, const double desired_sl, string &reason)
{
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   if(point <= 0.0)
   {
      reason = "NO_SYMBOL_POINT";
      return false;
   }
   double stop_level = (double)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL) * point;
   double freeze_level = (double)SymbolInfoInteger(symbol, SYMBOL_TRADE_FREEZE_LEVEL) * point;
   double min_distance = MathMax(stop_level, freeze_level);
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   if(type == POSITION_TYPE_BUY && desired_sl > bid - min_distance)
   {
      reason = "BUY_SL_TOO_CLOSE_TO_BID";
      return false;
   }
   if(type == POSITION_TYPE_SELL && desired_sl < ask + min_distance)
   {
      reason = "SELL_SL_TOO_CLOSE_TO_ASK";
      return false;
   }
   reason = "OK";
   return true;
}

void WriteManagementRow(
   const string action,
   const ulong ticket,
   const ENUM_POSITION_TYPE type,
   const double volume,
   const double open_price,
   const double initial_sl,
   const double current_sl,
   const double desired_sl,
   const double tp,
   const double unrealized_r,
   const double trigger_r,
   const double lock_r,
   const uint retcode,
   const string retcode_description,
   const string reason
)
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      _Symbol,
      InpCandidate,
      IntegerToString((int)InstanceMagic()),
      action,
      IntegerToString((int)ticket),
      type == POSITION_TYPE_BUY ? "BUY" : "SELL",
      DoubleToString(volume, 2),
      DoubleToString(open_price, digits),
      DoubleToString(initial_sl, digits),
      DoubleToString(current_sl, digits),
      DoubleToString(desired_sl, digits),
      DoubleToString(tp, digits),
      DoubleToString(unrealized_r, 4),
      DoubleToString(trigger_r, 2),
      DoubleToString(lock_r, 2),
      BoolText(InpProfitProtectionShadowOnly),
      IntegerToString((int)retcode),
      retcode_description,
      reason
   };
   AppendCsvRow(InpManagementLogFileName, row);
}

bool ModifyStopLossOnly(const ulong ticket, const double desired_sl, const double tp, MqlTradeResult &result)
{
   MqlTradeRequest request;
   ZeroMemory(request);
   ZeroMemory(result);
   request.action = TRADE_ACTION_SLTP;
   request.position = ticket;
   request.symbol = _Symbol;
   request.magic = InstanceMagic();
   request.sl = desired_sl;
   request.tp = tp;
   request.deviation = InpDeviationPoints;
   return OrderSend(request, result);
}

void ManageProfitProtectionForCurrentPosition()
{
   if(!InpProfitProtectionEnabled)
      return;
   if(PositionGetString(POSITION_SYMBOL) != _Symbol)
      return;
   if(PositionGetInteger(POSITION_MAGIC) != InstanceMagic())
      return;

   ulong ticket = (ulong)PositionGetInteger(POSITION_TICKET);
   ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
   double volume = PositionGetDouble(POSITION_VOLUME);
   double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
   double current_sl = PositionGetDouble(POSITION_SL);
   double tp = PositionGetDouble(POSITION_TP);
   double initial_sl = InitialStopForPosition(ticket, current_sl);
   double risk_price = PositionRiskPrice(type, open_price, initial_sl);
   if(risk_price <= 0.0)
   {
      WriteManagementRow("PROFIT_PROTECTION_SKIP_INVALID_INITIAL_RISK", ticket, type, volume, open_price, initial_sl, current_sl, current_sl, tp, 0.0, InpProfitProtectionTriggerR, InpProfitProtectionLockR, 0, "initial SL missing or invalid", "invalid_initial_risk");
      return;
   }

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double unrealized_r = PositionUnrealizedR(type, open_price, risk_price, bid, ask);
   if(unrealized_r < InpProfitProtectionTriggerR)
      return;

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double desired_sl = type == POSITION_TYPE_BUY
      ? open_price + InpProfitProtectionLockR * risk_price
      : open_price - InpProfitProtectionLockR * risk_price;
   desired_sl = NormalizeDouble(desired_sl, digits);
   if(!StopImprovesOnly(type, current_sl, desired_sl))
      return;

   string distance_reason = "";
   if(!StopRespectsBrokerDistance(type, _Symbol, desired_sl, distance_reason))
   {
      WriteManagementRow("PROFIT_PROTECTION_DEFER_STOPS_LEVEL", ticket, type, volume, open_price, initial_sl, current_sl, desired_sl, tp, unrealized_r, InpProfitProtectionTriggerR, InpProfitProtectionLockR, 0, distance_reason, "broker_distance");
      return;
   }

   if(KillSwitchActive())
   {
      WriteManagementRow("PROFIT_PROTECTION_KILL_SWITCH_BLOCK", ticket, type, volume, open_price, initial_sl, current_sl, desired_sl, tp, unrealized_r, InpProfitProtectionTriggerR, InpProfitProtectionLockR, 0, "kill switch active", "kill_switch_active");
      return;
   }

   if(InpProfitProtectionShadowOnly)
   {
      string shadow_state = ProfitProtectionStateName("P2EXP_PROTECTION_SHADOW_LOGGED", ticket);
      if(!GlobalVariableCheck(shadow_state))
      {
         GlobalVariableSet(shadow_state, TimeCurrent());
         WriteManagementRow("PROFIT_PROTECTION_SHADOW_WOULD_MOVE_SL", ticket, type, volume, open_price, initial_sl, current_sl, desired_sl, tp, unrealized_r, InpProfitProtectionTriggerR, InpProfitProtectionLockR, 0, "shadow only", "shadow_only");
      }
      return;
   }

   MqlTradeResult result;
   bool sent = ModifyStopLossOnly(ticket, desired_sl, tp, result);
   WriteManagementRow(sent ? "PROFIT_PROTECTION_SLTP_SENT" : "PROFIT_PROTECTION_SLTP_FAILED", ticket, type, volume, open_price, initial_sl, current_sl, desired_sl, tp, unrealized_r, InpProfitProtectionTriggerR, InpProfitProtectionLockR, result.retcode, result.comment, "profit_lock_triggered");
}

void ManageOpenPositions()
{
   if(!InpProfitProtectionEnabled)
      return;
   for(int index = PositionsTotal() - 1; index >= 0; index--)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      ManageProfitProtectionForCurrentPosition();
   }
}

int FamilyCodeForMagic(const long magic)
{
   if(magic >= 920100 && magic < 920300)
      return 1; // breakout-retest family
   if(magic >= 920300 && magic < 920500)
      return 2; // round-retest family
   if(magic >= 920500 && magic < 920600)
      return 3; // session-extreme family
   return 0;
}

int DirectionCodeFromObservation(const string direction_text)
{
   if(direction_text == "LONG" || direction_text == "BUY")
      return POSITION_TYPE_BUY;
   if(direction_text == "SHORT" || direction_text == "SELL")
      return POSITION_TYPE_SELL;
   return -1;
}

string CompactDateTimeForGlobalVariable(const datetime value)
{
   string text = TimeToString(value, TIME_DATE | TIME_SECONDS);
   StringReplace(text, ".", "");
   StringReplace(text, "-", "");
   StringReplace(text, ":", "");
   StringReplace(text, " ", "_");
   return text;
}

datetime CurrentM5BarStart()
{
   datetime bar_time = iTime(_Symbol, PERIOD_M5, 0);
   if(bar_time > 0)
      return bar_time;
   int period_seconds = PeriodSeconds(PERIOD_M5);
   if(period_seconds <= 0)
      period_seconds = 300;
   return (datetime)((long)(TimeCurrent() / period_seconds) * period_seconds);
}

string FamilyMutexDirectionToken(const string direction_text)
{
   int direction_code = DirectionCodeFromObservation(direction_text);
   if(direction_code == POSITION_TYPE_BUY)
      return "BUY";
   if(direction_code == POSITION_TYPE_SELL)
      return "SELL";
   return "NONE";
}

string FamilyMutexNameForObservation(const Phase1BreakoutRetestObservation &observation)
{
   int family = FamilyCodeForMagic(InstanceMagic());
   string direction = FamilyMutexDirectionToken(observation.direction_text);
   datetime bar_time = CurrentM5BarStart();
   if(family <= 0 || direction == "NONE" || bar_time <= 0)
      return "";
   return "FAMMUX_" + IntegerToString(family) + _Symbol + direction + CompactDateTimeForGlobalVariable(bar_time);
}

bool EnsureFamilyMutexSlot(const string mutex_name)
{
   if(mutex_name == "")
      return false;
   if(GlobalVariableCheck(mutex_name))
      return true;
   ResetLastError();
   if(GlobalVariableTemp(mutex_name))
      return true;
   if(GlobalVariableCheck(mutex_name))
      return true;
   Print("Could not create family mutex global variable ", mutex_name, " error=", GetLastError());
   return false;
}

void ExpireFamilyMutexClaim()
{
   if(g_family_mutex_claim_name == "")
      return;
   int period_seconds = PeriodSeconds(PERIOD_M5);
   if(period_seconds <= 0)
      period_seconds = 300;
   if(TimeCurrent() < g_family_mutex_claim_bar_time + period_seconds)
      return;
   if(GlobalVariableCheck(g_family_mutex_claim_name))
   {
      double owner = GlobalVariableGet(g_family_mutex_claim_name);
      if((long)owner == InstanceMagic())
         GlobalVariableDel(g_family_mutex_claim_name);
   }
   g_family_mutex_claim_name = "";
   g_family_mutex_claim_bar_time = 0;
}

bool ClaimFamilyMutexBeforeOrder(const Phase1BreakoutRetestObservation &observation, string &mutex_name)
{
   ExpireFamilyMutexClaim();
   mutex_name = FamilyMutexNameForObservation(observation);
   if(!EnsureFamilyMutexSlot(mutex_name))
      return false;
   long magic = InstanceMagic();
   ResetLastError();
   if(GlobalVariableSetOnCondition(mutex_name, (double)magic, 0.0))
   {
      g_family_mutex_claim_name = mutex_name;
      g_family_mutex_claim_bar_time = CurrentM5BarStart();
      return true;
   }
   double owner = GlobalVariableCheck(mutex_name) ? GlobalVariableGet(mutex_name) : 0.0;
   Print("Family mutex already claimed: ", mutex_name, " owner=", DoubleToString(owner, 0), " magic=", magic);
   return false;
}

bool RunFamilyMutexNamespaceSelfTest(string &status_text)
{
   string test_name = "FAMMUX_SELFTEST_"
      + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN))
      + "_" + _Symbol
      + "_" + IntegerToString((int)InstanceMagic())
      + "_" + CompactDateTimeForGlobalVariable(TimeGMT());
   if(GlobalVariableCheck(test_name))
      GlobalVariableDel(test_name);
   bool created = EnsureFamilyMutexSlot(test_name);
   bool claimed = false;
   bool deleted = false;
   double stored_value = 0.0;
   if(created)
   {
      ResetLastError();
      claimed = GlobalVariableSetOnCondition(test_name, (double)InstanceMagic(), 0.0);
      if(GlobalVariableCheck(test_name))
         stored_value = GlobalVariableGet(test_name);
      deleted = GlobalVariableDel(test_name);
   }
   bool passed = created && claimed && ((long)stored_value == InstanceMagic()) && deleted;
   status_text = passed
      ? "GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=" + test_name
      : "GV_MUTEX_NAMESPACE_SELF_TEST_FAIL name=" + test_name
         + " created=" + BoolText(created)
         + " claimed=" + BoolText(claimed)
         + " deleted=" + BoolText(deleted);
   return passed;
}

bool SameFamilySameDirectionOpenOnCurrentM5Bar(const Phase1BreakoutRetestObservation &observation)
{
   int wanted_direction = DirectionCodeFromObservation(observation.direction_text);
   if(wanted_direction < 0)
      return false;
   int wanted_family = FamilyCodeForMagic(InstanceMagic());
   if(wanted_family <= 0)
      return false;

   datetime bar_start = iTime(_Symbol, PERIOD_M5, 0);
   int bar_seconds = PeriodSeconds(PERIOD_M5);
   if(bar_start <= 0 || bar_seconds <= 0)
      return false;
   datetime bar_end = bar_start + bar_seconds;

   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol)
         continue;
      if((int)PositionGetInteger(POSITION_TYPE) != wanted_direction)
         continue;
      if(FamilyCodeForMagic(PositionGetInteger(POSITION_MAGIC)) != wanted_family)
         continue;
      datetime open_time = (datetime)PositionGetInteger(POSITION_TIME);
      if(open_time >= bar_start && open_time < bar_end)
         return true;
   }

   for(int index = 0; index < OrdersTotal(); index++)
   {
      ulong ticket = OrderGetTicket(index);
      if(ticket == 0)
         continue;
      if(!OrderSelect(ticket))
         continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol)
         continue;
      long order_type = OrderGetInteger(ORDER_TYPE);
      bool buy_order = order_type == ORDER_TYPE_BUY || order_type == ORDER_TYPE_BUY_LIMIT || order_type == ORDER_TYPE_BUY_STOP || order_type == ORDER_TYPE_BUY_STOP_LIMIT;
      bool sell_order = order_type == ORDER_TYPE_SELL || order_type == ORDER_TYPE_SELL_LIMIT || order_type == ORDER_TYPE_SELL_STOP || order_type == ORDER_TYPE_SELL_STOP_LIMIT;
      if((wanted_direction == POSITION_TYPE_BUY && !buy_order) || (wanted_direction == POSITION_TYPE_SELL && !sell_order))
         continue;
      if(FamilyCodeForMagic(OrderGetInteger(ORDER_MAGIC)) != wanted_family)
         continue;
      datetime setup_time = (datetime)OrderGetInteger(ORDER_TIME_SETUP);
      if(setup_time >= bar_start && setup_time < bar_end)
         return true;
   }
   return false;
}

string InstanceComment()
{
   string candidate = InpCandidate;
   StringReplace(candidate, "symbol_normalized_round_retest_v0", "sn_round");
   StringReplace(candidate, "swing_breakout_retest_v0", "swing_br");
   StringReplace(candidate, "round_number_retest_v0", "round");
   StringReplace(candidate, "session_extreme_retest_v0", "sess_ext");
   StringReplace(candidate, "breakout_retest", "br");
   string comment = "P2DEMO_" + candidate + "_" + _Symbol;
   return StringSubstr(comment, 0, 31);
}

double NormalizeVolumeForSymbol(const double requested)
{
   double min_volume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_volume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double volume = requested;
   if(min_volume > 0.0 && volume < min_volume)
      volume = min_volume;
   if(max_volume > 0.0 && volume > max_volume)
      volume = max_volume;
   if(step > 0.0)
      volume = MathFloor(volume / step) * step;
   int digits = 2;
   if(step > 0.0 && step < 0.01)
      digits = 3;
   if(step > 0.0 && step < 0.001)
      digits = 4;
   return NormalizeDouble(volume, digits);
}

double EffectiveFixedLot()
{
   if(_Symbol == "EURUSD")
      return InpEURUSDFixedLot;
   if(_Symbol == "GBPUSD")
      return InpGBPUSDFixedLot;
   return InpFixedLot;
}

ENUM_ORDER_TYPE_FILLING FillPolicy()
{
   int filling = (int)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if((filling & SYMBOL_FILLING_IOC) == SYMBOL_FILLING_IOC)
      return ORDER_FILLING_IOC;
   if((filling & SYMBOL_FILLING_FOK) == SYMBOL_FILLING_FOK)
      return ORDER_FILLING_FOK;
   return ORDER_FILLING_RETURN;
}

int CountOpenExposureForInstance()
{
   long magic = InstanceMagic();
   int count = 0;
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == magic)
         count++;
   }
   for(int index = 0; index < OrdersTotal(); index++)
   {
      ulong ticket = OrderGetTicket(index);
      if(ticket == 0)
         continue;
      if(!OrderSelect(ticket))
         continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == magic)
         count++;
   }
   return count;
}

void ResetDailyOrderCounterIfNeeded()
{
   string today = TimeToString(TimeCurrent(), TIME_DATE);
   if(today != g_order_day_key)
   {
      g_order_day_key = today;
      g_orders_today = 0;
   }
}

void WriteOrderLogRow(
   const string action,
   const string direction,
   const double volume,
   const double request_price,
   const double sl,
   const double tp,
   const MqlTradeResult &result,
   const string reason_code,
   const string guard_reason,
   const string order_mode,
   const double spread_at_signal_points,
   const double spread_at_order_points,
   const double signal_entry_price,
   const double estimated_cost_r,
   const double stop_distance_points
)
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   string dirstate_direction = "0";
   string dirstate_regime = "UNKNOWN";
   string dirstate_strength = "0.000";
   DirectionStateShadowFieldsForLog(dirstate_direction, dirstate_regime, dirstate_strength, InpDirectionStateFileName);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double slippage_points = (point > 0.0 && result.price > 0.0 && request_price > 0.0)
      ? MathAbs(result.price - request_price) / point
      : 0.0;
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpFamilyLifecycleStatus,
      InpFamilyLifecycleStatus,
      "true",
      "false",
      "false",
      IntegerToString((int)InstanceMagic()),
      BoolText(InpBrokerActionAllowed),
      BoolText(InpDryRunOnly),
      BoolText(StringLen(TrimToken(InpCostSuspensionAcknowledgementToken)) > 0),
      action,
      direction,
      DoubleToString(volume, 2),
      order_mode,
      DoubleToString(spread_at_signal_points, 2),
      DoubleToString(spread_at_order_points, 2),
      DoubleToString(signal_entry_price, digits),
      DoubleToString(request_price, digits),
      DoubleToString(request_price, digits),
      DoubleToString(sl, digits),
      DoubleToString(tp, digits),
      IntegerToString((int)result.retcode),
      result.comment,
      IntegerToString((int)result.order),
      IntegerToString((int)result.deal),
      DoubleToString(result.price, digits),
      DoubleToString(result.volume, 2),
      DoubleToString(slippage_points, 2),
      DoubleToString(estimated_cost_r, 4),
      DoubleToString(stop_distance_points, 2),
      IntegerToString(AccountOrdersToday()),
      IntegerToString(CountOpenExposureForAccount()),
      reason_code,
      guard_reason,
      dirstate_direction,
      dirstate_regime,
      dirstate_strength
   };
   AppendCsvRow(InpOrderLogFileName, row);
}

bool TradingGuardsPass(
   const Phase1BreakoutRetestObservation &observation,
   const double spread_points,
   const double estimated_cost_r,
   string &guard_reason
)
{
   ResetDailyOrderCounterIfNeeded();
   if(InpDryRunOnly)
   {
      guard_reason = "dry_run_only_true";
      return false;
   }
   if(!InpBrokerActionAllowed)
   {
      guard_reason = "broker_action_not_allowed";
      return false;
   }
   if(KillSwitchActive())
   {
      guard_reason = "kill_switch_active";
      return false;
   }
   if(!ExperimentalAuthorizationTokenValid())
   {
      guard_reason = "experimental_authorization_token_missing_or_invalid";
      return false;
   }
   if(!CostSuspensionAcknowledgementTokenValid())
   {
      guard_reason = "cost_suspension_acknowledgement_token_missing_or_invalid";
      return false;
   }
   if(!AccountLoginWhitelisted())
   {
      guard_reason = "account_login_not_whitelisted";
      return false;
   }
   if(!CandidateExecutionAuthorized())
   {
      guard_reason = "candidate_not_explicitly_authorized";
      return false;
   }
   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
   {
      guard_reason = "not_demo_server";
      return false;
   }
   if(!AccountTradeModeDemo())
   {
      guard_reason = "account_trade_mode_not_demo";
      return false;
   }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
   {
      guard_reason = "terminal_or_account_trading_disabled";
      return false;
   }
   if(!observation.would_signal)
   {
      guard_reason = "no_signal";
      return false;
   }
   if(!DirectionModeAllows(observation.direction_text))
   {
      guard_reason = "direction_mode_block";
      return false;
   }
   if(!ServerHourInTradeSession())
   {
      guard_reason = "server_hour_session_gate";
      return false;
   }
   string smart_trend_reason = "";
   bool smart_trend_pass = SmartTrendFilterPass(observation, smart_trend_reason);
   if(InpSmartTrendFilterEnabled && !InpSmartTrendFilterShadowOnly && !smart_trend_pass)
   {
      guard_reason = smart_trend_reason;
      return false;
   }
   if(observation.entry_price <= 0.0 || observation.stop_loss <= 0.0 || observation.take_profit <= 0.0)
   {
      guard_reason = "missing_entry_sl_tp";
      return false;
   }
   if(InpMaxMeasuredSpreadPoints > 0.0 && spread_points > InpMaxMeasuredSpreadPoints)
   {
      guard_reason = "measured_spread_points_exceeds_threshold";
      return false;
   }
   if(InpMaxEstimatedCostR > 0.0 && estimated_cost_r > InpMaxEstimatedCostR)
   {
      guard_reason = "estimated_cost_r_exceeds_threshold";
      return false;
   }
   string fast_stopout_reason = "";
   bool fast_stopout_pass = FastStopoutFilterPass(observation, fast_stopout_reason);
   if(InpFastStopoutFilterEnabled && !InpFastStopoutFilterShadowOnly && !fast_stopout_pass)
   {
      guard_reason = fast_stopout_reason;
      return false;
   }
   if(InpMaxOrdersPerDay > 0 && g_orders_today >= InpMaxOrdersPerDay)
   {
      guard_reason = "max_orders_per_day_reached";
      return false;
   }
   if(InpMaxAccountOrdersPerDay > 0 && AccountOrdersToday() >= InpMaxAccountOrdersPerDay)
   {
      guard_reason = "max_account_orders_per_day_reached";
      return false;
   }
   if(InpMinSecondsBetweenOrders > 0 && g_last_order_submit_time > 0 && TimeCurrent() - g_last_order_submit_time < InpMinSecondsBetweenOrders)
   {
      guard_reason = "min_seconds_between_orders";
      return false;
   }
   if(SameFamilySameDirectionOpenOnCurrentM5Bar(observation))
   {
      guard_reason = "WOULD_DUPLICATE_FAMILY_EVENT";
      return false;
   }
   if(InpMaxOpenPositionsPerInstance > 0 && CountOpenExposureForInstance() >= InpMaxOpenPositionsPerInstance)
   {
      guard_reason = "open_instance_exposure_exists";
      return false;
   }
   if(InpMaxOpenPositionsPerMagic > 0 && CountOpenExposureForInstance() >= InpMaxOpenPositionsPerMagic)
   {
      guard_reason = "open_magic_exposure_exists";
      return false;
   }
   guard_reason = "pass";
   return true;
}

bool SendDemoMarketOrder(const Phase1BreakoutRetestObservation &observation)
{
   string guard_reason = "";
   MqlTradeResult result;
   ZeroMemory(result);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double spread_at_signal_points = CurrentSpreadPoints();
   double estimated_cost_r_signal = EstimatedCostRForObservation(observation, spread_at_signal_points);
   if(!TradingGuardsPass(observation, spread_at_signal_points, estimated_cost_r_signal, guard_reason))
   {
      WriteOrderLogRow(
         "GUARD_BLOCK",
         observation.direction_text,
         0.0,
         0.0,
         0.0,
         0.0,
         result,
         observation.reason_code,
         guard_reason,
         "MARKET_PROXY",
         spread_at_signal_points,
         spread_at_signal_points,
         observation.entry_price,
         estimated_cost_r_signal,
         observation.stop_distance_points
      );
      return false;
   }

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   bool is_long = observation.direction_text == "LONG";
   double price = is_long ? ask : bid;
   double signal_risk = MathAbs(observation.entry_price - observation.stop_loss);
   int stops_level = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_distance = (stops_level + 5) * point;
   double spread_distance = MathAbs(ask - bid);
   if(spread_distance > 0.0 && min_distance < 3.0 * spread_distance)
      min_distance = 3.0 * spread_distance;
   if(point <= 0.0001 && min_distance < 100.0 * point)
      min_distance = 100.0 * point;
   if(_Symbol == "XAUUSD" && min_distance < 300.0 * point)
      min_distance = 300.0 * point;
   if(signal_risk < min_distance)
      signal_risk = min_distance;
   if(signal_risk <= 0.0 || price <= 0.0)
   {
      guard_reason = "invalid_price_or_risk";
      WriteOrderLogRow("GUARD_BLOCK", observation.direction_text, 0.0, price, 0.0, 0.0, result, observation.reason_code, guard_reason, "MARKET_PROXY", spread_at_signal_points, spread_at_signal_points, observation.entry_price, 0.0, observation.stop_distance_points);
      return false;
   }
   double stop_distance_points = point > 0.0 ? signal_risk / point : 0.0;

   double sl = is_long ? price - signal_risk : price + signal_risk;
   double tp = is_long ? price + 1.50 * signal_risk : price - 1.50 * signal_risk;
   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);
   price = NormalizeDouble(price, digits);
   double volume = NormalizeVolumeForSymbol(EffectiveFixedLot());
   if(volume <= 0.0)
   {
      guard_reason = "invalid_volume";
      WriteOrderLogRow("GUARD_BLOCK", observation.direction_text, 0.0, price, sl, tp, result, observation.reason_code, guard_reason, "MARKET_PROXY", spread_at_signal_points, spread_at_signal_points, observation.entry_price, 0.0, stop_distance_points);
      return false;
   }

   string mutex_name = "";
   if(!ClaimFamilyMutexBeforeOrder(observation, mutex_name))
   {
      guard_reason = mutex_name == "" ? "family_mutex_context_unavailable" : "WOULD_DUPLICATE_FAMILY_EVENT";
      WriteOrderLogRow("GUARD_BLOCK", observation.direction_text, 0.0, price, sl, tp, result, observation.reason_code, guard_reason, "MARKET_PROXY", spread_at_signal_points, spread_at_signal_points, observation.entry_price, estimated_cost_r_signal, stop_distance_points);
      return false;
   }

   MqlTradeRequest request;
   ZeroMemory(request);
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.magic = InstanceMagic();
   request.volume = volume;
   request.type = is_long ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   request.price = price;
   request.sl = sl;
   request.tp = tp;
   request.deviation = InpDeviationPoints;
   request.type_filling = FillPolicy();
   request.type_time = ORDER_TIME_GTC;
   request.comment = InstanceComment();

   bool sent = OrderSend(request, result);
   string action = sent ? "ORDER_SEND_OK" : "ORDER_SEND_FAIL";
   if(sent && (result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED || result.retcode == TRADE_RETCODE_DONE_PARTIAL))
   {
      g_last_order_submit_time = TimeCurrent();
      g_orders_today++;
      IncrementAccountOrdersToday();
   }
   double spread_at_order_points = CurrentSpreadPoints();
   double estimated_cost_r = signal_risk > 0.0 ? (spread_at_order_points * point / signal_risk) : 0.0;
   WriteOrderLogRow(
      action,
      observation.direction_text,
      volume,
      price,
      sl,
      tp,
      result,
      observation.reason_code,
      guard_reason,
      "MARKET_PROXY",
      spread_at_signal_points,
      spread_at_order_points,
      observation.entry_price,
      estimated_cost_r,
      stop_distance_points
   );
   return sent;
}

int OnInit()
{
   if(InpDryRunOnly || !InpBrokerActionAllowed)
   {
      Print("Phase2ExperimentalDemoExecutor refused to start because broker-action mode was not explicitly enabled.");
      return INIT_FAILED;
   }

   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
   {
      Print("Phase2ExperimentalDemoExecutor refused to start outside the expected demo server. Server=", server);
      return INIT_FAILED;
   }

   if(!ExperimentalAuthorizationTokenValid())
   {
      Print("Phase2ExperimentalDemoExecutor refused to start without a valid experimental authorization token.");
      return INIT_FAILED;
   }

   if(!CostSuspensionAcknowledgementTokenValid())
   {
      Print("Phase2ExperimentalDemoExecutor refused to start without a valid cost-suspension acknowledgement token.");
      return INIT_FAILED;
   }

   if(!AccountLoginWhitelisted())
   {
      Print("Phase2ExperimentalDemoExecutor refused account login ", (int)AccountInfoInteger(ACCOUNT_LOGIN), " because it is not in InpAllowedAccountLoginsCsv.");
      return INIT_FAILED;
   }

   if(_Symbol != InpTargetSymbol)
   {
      Print("Phase2ExperimentalDemoExecutor attached to ", _Symbol, " but target is ", InpTargetSymbol);
      return INIT_FAILED;
   }

   if(!CsvContainsSymbol(InpQualifiedSymbolsCsv, _Symbol))
   {
      Print("Phase2ExperimentalDemoExecutor refused symbol ", _Symbol, " because it is not qualified for ", InpCandidate);
      return INIT_FAILED;
   }

   if(!IsAllowedCandidate(InpCandidate))
   {
      Print("Phase2ExperimentalDemoExecutor refused unknown candidate ", InpCandidate);
      return INIT_FAILED;
   }

   if(!CandidateExecutionAuthorized())
   {
      Print("Phase2ExperimentalDemoExecutor refused candidate ", InpCandidate, " because it is not explicitly authorized.");
      return INIT_FAILED;
   }

   if(KillSwitchActive())
   {
      Print("Phase2ExperimentalDemoExecutor refused to start because the kill switch is active.");
      return INIT_FAILED;
   }

   if(!EnsureAttachmentLogHeader() || !EnsureStartupLogHeader() || !EnsureOrderLogHeader() || !EnsureManagementLogHeader())
      return INIT_FAILED;

   string gv_mutex_self_test_status = "";
   if(!RunFamilyMutexNamespaceSelfTest(gv_mutex_self_test_status))
   {
      WriteStartupRow(gv_mutex_self_test_status);
      return INIT_FAILED;
   }
   WriteStartupRow(gv_mutex_self_test_status);

   g_breakout_observer.ConfigureForSymbol(_Symbol, CandidateUsesSwingObserver(InpCandidate));
   ResetDailyOrderCounterIfNeeded();
   WriteStartupRow("ATTACHED_DEMO_EXECUTOR_ENABLED");
   A3MlShadowTapWriteRow("STARTUP", InpRunId, InpDryRunOnly, InpBrokerActionAllowed, InpCandidate, "ON_INIT", "NONE", false, "ATTACHED_DEMO_EXECUTOR_ENABLED", "PASS");
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ExpireFamilyMutexClaim();
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpFamilyLifecycleStatus,
      InpQualifiedSymbolsCsv,
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      InpAllowedAccountLoginsCsv,
      InpAuthorizedCandidatesCsv,
      BoolText(InpDryRunOnly),
      BoolText(InpBrokerActionAllowed),
      BoolText(CandidateHasNativeObserver(InpCandidate)),
      BoolText(StringLen(TrimToken(InpExperimentalAuthorizationToken)) > 0),
      BoolText(StringLen(TrimToken(InpCostSuspensionAcknowledgementToken)) > 0),
      IntegerToString(InpMaxAccountOrdersPerDay),
      "UNLIMITED",
      InpKillSwitchFileName,
      "REMOVED_REASON_" + IntegerToString(reason)
   };
   AppendCsvRow(InpStartupLogFileName, row);
}

void OnTick()
{
   ManageOpenPositions();
}

void OnTimer()
{
   ManageOpenPositions();
   ExpireFamilyMutexClaim();
   datetime m5_bar_time = iTime(_Symbol, PERIOD_M5, 0);
   if(m5_bar_time <= 0 || m5_bar_time == g_last_m5_bar_time)
      return;
   g_last_m5_bar_time = m5_bar_time;

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double spread_points = point > 0.0 ? (ask - bid) / point : 0.0;

   Phase1BreakoutRetestObservation observation;
   Phase1ResetBreakoutRetestObservation(observation);
   bool observer_supported = CandidateHasNativeObserver(InpCandidate);
   if(InpCandidate == "breakout_retest" || InpCandidate == "swing_breakout_retest_v0")
   {
      g_breakout_observer.Evaluate(_Symbol, point, observation);
   }
   else if(observer_supported)
   {
      EvaluateExperimentalRetestObserver(InpCandidate, _Symbol, point, observation);
   }
   else
   {
      observation.stage = "ATTACHED_OBSERVER_PENDING_IMPL";
      observation.reason_code = "candidate_attached_no_mql_observer_yet";
      observation.direction_text = "NONE";
   }

   string dirstate_direction = "0";
   string dirstate_regime = "UNKNOWN";
   string dirstate_strength = "0.000";
   DirectionStateShadowFieldsForLog(dirstate_direction, dirstate_regime, dirstate_strength, InpDirectionStateFileName);
   string ml_shadow_guard_reason = observation.would_signal ? "PENDING_TRADING_GUARDS" : "NO_SIGNAL";
   A3MlShadowTapWriteRow("SIGNAL", InpRunId, InpDryRunOnly, InpBrokerActionAllowed, InpCandidate, observation.stage, observation.direction_text, observation.would_signal, observation.reason_code, ml_shadow_guard_reason);

   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpFamilyLifecycleStatus,
      BoolText(CsvContainsSymbol(InpQualifiedSymbolsCsv, _Symbol)),
      BoolText(InpDryRunOnly),
      BoolText(InpBrokerActionAllowed),
      BoolText(observer_supported),
      TimeToString(m5_bar_time, TIME_DATE | TIME_SECONDS),
      DoubleToString(bid, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(ask, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(spread_points, 2),
      observation.stage,
      observation.direction_text,
      BoolText(observation.would_signal),
      observation.reason_code,
      observation.level_kind,
      DoubleToString(observation.level_price, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.entry_price, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.stop_loss, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.take_profit, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.stop_distance_points, 2),
      dirstate_direction,
      dirstate_regime,
      dirstate_strength
   };
   AppendCsvRow(InpAttachmentLogFileName, row);
   if(observation.would_signal)
      SendDemoMarketOrder(observation);
}
