#property strict
#property version   "1.000"
#property description "Trend-guarded fix observer. Telemetry only; no broker actions or order placement."

#include <Phase1/Phase1Types.mqh>
#include <Phase1/Phase1BreakoutRetest.mqh>

input string InpRunId = "phase2-trend-guarded-fix-observer-v0.1";
input bool InpDryRunOnly = true;
input string InpCandidate = "breakout_retest";
input string InpCandidateStatus = "TREND_GUARDED_FIX_OBSERVER_V2";
input string InpTargetSymbol = "XAUUSD";
input string InpQualifiedSymbolsCsv = "XAUUSD";
input string InpExpectedServerMarker = "Demo";
input string InpShadowPolicyVersion = "trend_guarded_fix_policy_20260612_v2";
input string InpAttachmentLogFileName = "trend_guarded_fix_observer_v2_signal_log.csv";
input string InpStartupLogFileName = "trend_guarded_fix_observer_v2_startup.csv";
input bool InpTrendVetoEnabled = true;
input int InpTrendSlopeLookbackBars = 3;
input double InpMinSlopePoints = 50.0;
input int InpDubaiUtcOffsetMinutes = 240;

CPhase1BreakoutRetestObserver g_breakout_observer;
datetime g_last_m5_bar_time = 0;
const bool BROKER_ACTION_ALLOWED = false;
int g_m15_ema20_handle = INVALID_HANDLE;
int g_h1_ema20_handle = INVALID_HANDLE;
int g_d1_ema20_handle = INVALID_HANDLE;
int g_d1_ema50_handle = INVALID_HANDLE;

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

bool IsAllowedCandidate(const string candidate)
{
   return candidate == "breakout_retest"
      || candidate == "swing_breakout_retest_v0"
      || candidate == "symbol_normalized_round_retest_v0"
      || candidate == "round_number_retest_v0"
      || candidate == "session_extreme_retest_v0"
      || candidate == "session_extreme_retest_v0_repair_v1";
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
   return candidate == "session_extreme_retest_v0" || candidate == "session_extreme_retest_v0_repair_v1";
}

string DubaiTimeBucket(const datetime value)
{
   MqlDateTime parts;
   TimeToStruct(value, parts);
   if(parts.hour >= 6 && parts.hour <= 11)
      return "Morning 06:00-11:59";
   if(parts.hour >= 12 && parts.hour <= 15)
      return "Afternoon 12:00-15:59";
   if(parts.hour >= 16 && parts.hour <= 19)
      return "Evening 16:00-19:59";
   return "Night 20:00-05:59";
}

datetime DubaiNow()
{
   return TimeGMT() + InpDubaiUtcOffsetMinutes * 60;
}

bool IsXauSymbol(const string symbol_name)
{
   return StringFind(LowerText(symbol_name), "xauusd") >= 0;
}

bool ConfigureIndicatorHandles()
{
   g_m15_ema20_handle = iMA(_Symbol, PERIOD_M15, 20, 0, MODE_EMA, PRICE_CLOSE);
   g_h1_ema20_handle = iMA(_Symbol, PERIOD_H1, 20, 0, MODE_EMA, PRICE_CLOSE);
   g_d1_ema20_handle = iMA(_Symbol, PERIOD_D1, 20, 0, MODE_EMA, PRICE_CLOSE);
   g_d1_ema50_handle = iMA(_Symbol, PERIOD_D1, 50, 0, MODE_EMA, PRICE_CLOSE);
   return g_m15_ema20_handle != INVALID_HANDLE
      && g_h1_ema20_handle != INVALID_HANDLE
      && g_d1_ema20_handle != INVALID_HANDLE
      && g_d1_ema50_handle != INVALID_HANDLE;
}

void ReleaseIndicatorHandles()
{
   if(g_m15_ema20_handle != INVALID_HANDLE)
      IndicatorRelease(g_m15_ema20_handle);
   if(g_h1_ema20_handle != INVALID_HANDLE)
      IndicatorRelease(g_h1_ema20_handle);
   if(g_d1_ema20_handle != INVALID_HANDLE)
      IndicatorRelease(g_d1_ema20_handle);
   if(g_d1_ema50_handle != INVALID_HANDLE)
      IndicatorRelease(g_d1_ema50_handle);

   g_m15_ema20_handle = INVALID_HANDLE;
   g_h1_ema20_handle = INVALID_HANDLE;
   g_d1_ema20_handle = INVALID_HANDLE;
   g_d1_ema50_handle = INVALID_HANDLE;
}

bool CopyEmaValue(const int handle, const int shift, double &value)
{
   value = 0.0;
   if(handle == INVALID_HANDLE)
      return false;
   double buffer[];
   ArraySetAsSeries(buffer, true);
   int copied = CopyBuffer(handle, 0, shift, 1, buffer);
   if(copied != 1)
      return false;
   value = buffer[0];
   return value > 0.0;
}

bool EmaSlopePointsFromHandle(
   const int handle,
   const int lookback_bars,
   const double point,
   double &slope_points
)
{
   slope_points = 0.0;
   if(point <= 0.0 || lookback_bars <= 0)
      return false;

   double current_value = 0.0;
   double previous_value = 0.0;
   if(!CopyEmaValue(handle, 1, current_value))
      return false;
   if(!CopyEmaValue(handle, 1 + lookback_bars, previous_value))
      return false;
   slope_points = (current_value - previous_value) / point;
   return true;
}

string DailyBiasText(const string symbol_name, bool &bias_available)
{
   bias_available = false;
   double close_price = iClose(symbol_name, PERIOD_D1, 1);
   double ema20 = 0.0;
   double ema50 = 0.0;
   if(close_price <= 0.0 || !CopyEmaValue(g_d1_ema20_handle, 1, ema20) || !CopyEmaValue(g_d1_ema50_handle, 1, ema50))
      return "UNKNOWN";
   bias_available = true;
   if(close_price > ema20 && ema20 > ema50)
      return "BULLISH";
   if(close_price < ema20 && ema20 < ema50)
      return "BEARISH";
   return "MIXED";
}

string TrendVetoActionForObservation(
   const string symbol_name,
   const string direction,
   const bool would_signal,
   const bool m15_slope_available,
   const bool h1_slope_available,
   const double m15_ema20_slope_points,
   const double h1_ema20_slope_points
)
{
   if(!would_signal)
      return "KEEP_NO_SIGNAL";
   if(!InpTrendVetoEnabled)
      return "KEEP";
   if(!IsXauSymbol(symbol_name))
      return "KEEP";
   if(!m15_slope_available || !h1_slope_available)
      return "SLOPE_UNAVAILABLE";
   if(direction == "SHORT"
      && m15_ema20_slope_points >= InpMinSlopePoints
      && h1_ema20_slope_points >= InpMinSlopePoints)
      return "BLOCK";
   if(direction == "LONG"
      && m15_ema20_slope_points <= -InpMinSlopePoints
      && h1_ema20_slope_points <= -InpMinSlopePoints)
      return "BLOCK";
   return "KEEP";
}

string TrendVetoReasonForObservation(
   const string symbol_name,
   const string direction,
   const bool would_signal,
   const bool m15_slope_available,
   const bool h1_slope_available,
   const double m15_ema20_slope_points,
   const double h1_ema20_slope_points
)
{
   if(!would_signal)
      return "NO_SIGNAL";
   if(!InpTrendVetoEnabled)
      return "TREND_VETO_DISABLED";
   if(!IsXauSymbol(symbol_name))
      return "NON_XAU_NOT_TREND_GUARDED";
   if(!m15_slope_available && !h1_slope_available)
      return "SLOPE_UNAVAILABLE_M15_H1";
   if(!m15_slope_available)
      return "SLOPE_UNAVAILABLE_M15";
   if(!h1_slope_available)
      return "SLOPE_UNAVAILABLE_H1";
   if(direction == "SHORT"
      && m15_ema20_slope_points >= InpMinSlopePoints
      && h1_ema20_slope_points >= InpMinSlopePoints)
      return "BLOCK_XAUUSD_SHORT_UPTREND_M15_H1";
   if(direction == "LONG"
      && m15_ema20_slope_points <= -InpMinSlopePoints
      && h1_ema20_slope_points <= -InpMinSlopePoints)
      return "BLOCK_XAUUSD_LONG_DOWNTREND_M15_H1";
   return "KEEP_TREND_NOT_OPPOSED";
}

string FixedShadowActionForObservation(const bool would_signal, const string trend_veto_action)
{
   if(!would_signal)
      return "KEEP_NO_SIGNAL";
   if(trend_veto_action == "BLOCK")
      return "BLOCK";
   if(trend_veto_action == "SLOPE_UNAVAILABLE")
      return "SLOPE_UNAVAILABLE";
   return "KEEP";
}

string FixedShadowReasonForObservation(const bool would_signal, const string trend_veto_reason)
{
   if(!would_signal)
      return "NO_SIGNAL";
   return trend_veto_reason;
}

string AvailabilityText(const bool value)
{
   return value ? "OK" : "SLOPE_UNAVAILABLE";
}

string ShadowActionForObservation(
   const string candidate,
   const string symbol_name,
   const string time_bucket,
   const bool would_signal
)
{
   if(!would_signal)
      return "KEEP_NO_SIGNAL";
   if(candidate == "symbol_normalized_round_retest_v0")
      return "BLOCK";
   if(candidate == "session_extreme_retest_v0")
      return "BLOCK";
   if(IsXauSymbol(symbol_name) && (time_bucket == "Morning 06:00-11:59" || time_bucket == "Afternoon 12:00-15:59"))
      return "BLOCK";
   return "KEEP";
}

string ShadowReasonForObservation(
   const string candidate,
   const string symbol_name,
   const string time_bucket,
   const bool would_signal
)
{
   if(!would_signal)
      return "NO_SIGNAL";
   if(candidate == "symbol_normalized_round_retest_v0")
      return "BLOCK_WEAK_EA_SYMBOL_NORMALIZED_ROUND";
   if(candidate == "session_extreme_retest_v0")
      return "BLOCK_WEAK_EA_SESSION_EXTREME_RETEST";
   if(IsXauSymbol(symbol_name) && (time_bucket == "Morning 06:00-11:59" || time_bucket == "Afternoon 12:00-15:59"))
      return "BLOCK_XAUUSD_MORNING_AFTERNOON";
   return "KEEP";
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
   if(candidate == "session_extreme_retest_v0_repair_v1")
      return "SESSION_EXTREME_RETEST_REPAIR_V1";
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
      "timestamp_dubai",
      "run_id",
      "account_server",
      "symbol",
      "candidate",
      "candidate_status",
      "qualified_symbol",
      "dry_run",
      "broker_action_allowed",
      "shadow_policy_version",
      "observer_supported",
      "m5_bar_time",
      "time_bucket",
      "bid",
      "ask",
      "spread_points",
      "stage",
      "direction",
      "would_signal",
      "legacy_shadow_action",
      "legacy_shadow_reason",
      "d1_bias",
      "d1_bias_status",
      "m15_ema20_slope_points",
      "m15_ema20_slope_status",
      "h1_ema20_slope_points",
      "h1_ema20_slope_status",
      "atr14_m5_points",
      "estimated_cost_r",
      "m15_ema20_distance_points",
      "trend_veto_action",
      "trend_veto_reason",
      "fixed_shadow_action",
      "fixed_shadow_reason",
      "shadow_decision_view",
      "reason_code",
      "level_kind",
      "level_price",
      "entry_price",
      "stop_loss",
      "take_profit",
      "stop_distance_points"
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
      "timestamp_dubai",
      "run_id",
      "account_server",
      "symbol",
      "candidate",
      "candidate_status",
      "qualified_symbols",
      "dry_run",
      "broker_action_allowed",
      "shadow_policy_version",
      "dubai_utc_offset_minutes",
      "observer_supported",
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
      TimeToString(DubaiNow(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpQualifiedSymbolsCsv,
      BoolText(InpDryRunOnly),
      BoolText(BROKER_ACTION_ALLOWED),
      InpShadowPolicyVersion,
      IntegerToString(InpDubaiUtcOffsetMinutes),
      BoolText(CandidateHasNativeObserver(InpCandidate)),
      status_text
   };
   return AppendCsvRow(InpStartupLogFileName, row);
}

int OnInit()
{
   if(!InpDryRunOnly)
   {
      Print("Phase2TrendGuardedFixObserver refused to start because dry-run mode is locked.");
      return INIT_FAILED;
   }

   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
   {
      Print("Phase2TrendGuardedFixObserver refused to start outside the expected demo server. Server=", server);
      return INIT_FAILED;
   }

   if(_Symbol != InpTargetSymbol)
   {
      Print("Phase2TrendGuardedFixObserver attached to ", _Symbol, " but target is ", InpTargetSymbol);
      return INIT_FAILED;
   }

   if(!CsvContainsSymbol(InpQualifiedSymbolsCsv, _Symbol))
   {
      Print("Phase2TrendGuardedFixObserver refused symbol ", _Symbol, " because it is not qualified for ", InpCandidate);
      return INIT_FAILED;
   }

   if(!IsAllowedCandidate(InpCandidate))
   {
      Print("Phase2TrendGuardedFixObserver refused unknown candidate ", InpCandidate);
      return INIT_FAILED;
   }

   if(!ConfigureIndicatorHandles())
   {
      Print("Phase2TrendGuardedFixObserver refused to start because trend indicator handles could not be created.");
      ReleaseIndicatorHandles();
      return INIT_FAILED;
   }

   if(!EnsureAttachmentLogHeader() || !EnsureStartupLogHeader())
   {
      ReleaseIndicatorHandles();
      return INIT_FAILED;
   }

   g_breakout_observer.Configure(CandidateUsesSwingObserver(InpCandidate));
   WriteStartupRow("ATTACHED_TREND_GUARDED_FIX_TELEMETRY_ONLY");
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ReleaseIndicatorHandles();
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      TimeToString(DubaiNow(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpQualifiedSymbolsCsv,
      BoolText(InpDryRunOnly),
      BoolText(BROKER_ACTION_ALLOWED),
      InpShadowPolicyVersion,
      IntegerToString(InpDubaiUtcOffsetMinutes),
      BoolText(CandidateHasNativeObserver(InpCandidate)),
      "REMOVED_REASON_" + IntegerToString(reason)
   };
   AppendCsvRow(InpStartupLogFileName, row);
}

void OnTimer()
{
   datetime m5_bar_time = iTime(_Symbol, PERIOD_M5, 0);
   if(m5_bar_time <= 0 || m5_bar_time == g_last_m5_bar_time)
      return;
   g_last_m5_bar_time = m5_bar_time;

   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double spread_points = point > 0.0 ? (ask - bid) / point : 0.0;
   datetime dubai_time = DubaiNow();
   string time_bucket = DubaiTimeBucket(dubai_time);

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
   double m15_ema20_slope_points = 0.0;
   double h1_ema20_slope_points = 0.0;
   bool m15_slope_available = EmaSlopePointsFromHandle(
      g_m15_ema20_handle,
      InpTrendSlopeLookbackBars,
      point,
      m15_ema20_slope_points
   );
   bool h1_slope_available = EmaSlopePointsFromHandle(
      g_h1_ema20_handle,
      InpTrendSlopeLookbackBars,
      point,
      h1_ema20_slope_points
   );
   bool d1_bias_available = false;
   string d1_bias = DailyBiasText(_Symbol, d1_bias_available);
   double atr14_m5_points = point > 0.0 ? AverageRangePrice(_Symbol, PERIOD_M5, 14, 1) / point : 0.0;
   double estimated_cost_r = observation.stop_distance_points > 0.0 ? spread_points / observation.stop_distance_points : 0.0;
   double m15_ema20_value = 0.0;
   bool m15_ema20_value_available = CopyEmaValue(g_m15_ema20_handle, 1, m15_ema20_value);
   double closed_m5_price = iClose(_Symbol, PERIOD_M5, 1);
   double m15_ema20_distance_points = (m15_ema20_value_available && closed_m5_price > 0.0 && point > 0.0)
      ? (closed_m5_price - m15_ema20_value) / point
      : 0.0;
   string legacy_shadow_action = ShadowActionForObservation(InpCandidate, _Symbol, time_bucket, observation.would_signal);
   string legacy_shadow_reason = ShadowReasonForObservation(InpCandidate, _Symbol, time_bucket, observation.would_signal);
   string trend_veto_action = TrendVetoActionForObservation(
      _Symbol,
      observation.direction_text,
      observation.would_signal,
      m15_slope_available,
      h1_slope_available,
      m15_ema20_slope_points,
      h1_ema20_slope_points
   );
   string trend_veto_reason = TrendVetoReasonForObservation(
      _Symbol,
      observation.direction_text,
      observation.would_signal,
      m15_slope_available,
      h1_slope_available,
      m15_ema20_slope_points,
      h1_ema20_slope_points
   );
   string fixed_shadow_action = FixedShadowActionForObservation(observation.would_signal, trend_veto_action);
   string fixed_shadow_reason = FixedShadowReasonForObservation(observation.would_signal, trend_veto_reason);

   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      TimeToString(dubai_time, TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      BoolText(CsvContainsSymbol(InpQualifiedSymbolsCsv, _Symbol)),
      BoolText(InpDryRunOnly),
      BoolText(BROKER_ACTION_ALLOWED),
      InpShadowPolicyVersion,
      BoolText(observer_supported),
      TimeToString(m5_bar_time, TIME_DATE | TIME_SECONDS),
      time_bucket,
      DoubleToString(bid, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(ask, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(spread_points, 2),
      observation.stage,
      observation.direction_text,
      BoolText(observation.would_signal),
      legacy_shadow_action,
      legacy_shadow_reason,
      d1_bias,
      d1_bias_available ? "OK" : "D1_BIAS_UNAVAILABLE",
      DoubleToString(m15_ema20_slope_points, 2),
      AvailabilityText(m15_slope_available),
      DoubleToString(h1_ema20_slope_points, 2),
      AvailabilityText(h1_slope_available),
      DoubleToString(atr14_m5_points, 2),
      DoubleToString(estimated_cost_r, 4),
      m15_ema20_value_available ? DoubleToString(m15_ema20_distance_points, 2) : "EMA_UNAVAILABLE",
      trend_veto_action,
      trend_veto_reason,
      fixed_shadow_action,
      fixed_shadow_reason,
      "trend_guarded_shadow_forward_view",
      observation.reason_code,
      observation.level_kind,
      DoubleToString(observation.level_price, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.entry_price, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.stop_loss, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.take_profit, (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS)),
      DoubleToString(observation.stop_distance_points, 2)
   };
   AppendCsvRow(InpAttachmentLogFileName, row);
}
