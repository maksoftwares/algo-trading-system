#property strict
#property version   "1.000"
#property description "Experimental demo observer attachment. Telemetry only; no broker actions."

#include <Phase1/Phase1Types.mqh>
#include <Phase1/Phase1BreakoutRetest.mqh>

input string InpRunId = "phase2-experimental-demo-observer-v0.1";
input bool InpDryRunOnly = true;
input string InpCandidate = "breakout_retest";
input string InpCandidateStatus = "ACCEPTED";
input string InpTargetSymbol = "XAUUSD";
input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,USDJPY";
input string InpExpectedServerMarker = "Demo";
input string InpAttachmentLogFileName = "experimental_demo_attachment_log.csv";
input string InpStartupLogFileName = "experimental_demo_attachment_startup.csv";

CPhase1BreakoutRetestObserver g_breakout_observer;
datetime g_last_m5_bar_time = 0;

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
      "run_id",
      "account_server",
      "symbol",
      "candidate",
      "candidate_status",
      "qualified_symbols",
      "dry_run",
      "broker_action_allowed",
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
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpQualifiedSymbolsCsv,
      BoolText(InpDryRunOnly),
      "false",
      BoolText(CandidateHasNativeObserver(InpCandidate)),
      status_text
   };
   return AppendCsvRow(InpStartupLogFileName, row);
}

int OnInit()
{
   if(!InpDryRunOnly)
   {
      Print("Phase2ExperimentalDemoObserver refused to start because dry-run mode is locked.");
      return INIT_FAILED;
   }

   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
   {
      Print("Phase2ExperimentalDemoObserver refused to start outside the expected demo server. Server=", server);
      return INIT_FAILED;
   }

   if(_Symbol != InpTargetSymbol)
   {
      Print("Phase2ExperimentalDemoObserver attached to ", _Symbol, " but target is ", InpTargetSymbol);
      return INIT_FAILED;
   }

   if(!CsvContainsSymbol(InpQualifiedSymbolsCsv, _Symbol))
   {
      Print("Phase2ExperimentalDemoObserver refused symbol ", _Symbol, " because it is not qualified for ", InpCandidate);
      return INIT_FAILED;
   }

   if(!IsAllowedCandidate(InpCandidate))
   {
      Print("Phase2ExperimentalDemoObserver refused unknown candidate ", InpCandidate);
      return INIT_FAILED;
   }

   if(!EnsureAttachmentLogHeader() || !EnsureStartupLogHeader())
      return INIT_FAILED;

   g_breakout_observer.Configure(CandidateUsesSwingObserver(InpCandidate));
   WriteStartupRow("ATTACHED_DEMO_TELEMETRY_ONLY");
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      InpQualifiedSymbolsCsv,
      BoolText(InpDryRunOnly),
      "false",
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

   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      _Symbol,
      InpCandidate,
      InpCandidateStatus,
      BoolText(CsvContainsSymbol(InpQualifiedSymbolsCsv, _Symbol)),
      BoolText(InpDryRunOnly),
      "false",
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
      DoubleToString(observation.stop_distance_points, 2)
   };
   AppendCsvRow(InpAttachmentLogFileName, row);
}
