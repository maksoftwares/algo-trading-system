// NON_CANONICAL / EXPERIMENTAL DEMO ONLY / DO NOT DEPLOY AS PHASE2.
// This file contains guarded demo broker-action logic for a quarantined owner-requested
// experiment. It is not part of the canonical Phase 1 dry-run shell, cannot authorize
// Phase 2, and must remain excluded from canonical deploy/compile bundles.
#property strict
#property version   "1.000"
#property description "Experimental demo repair executor attachment. Demo account only; sends small guarded repaired-lane orders."

#include <Phase1/Phase1Types.mqh>
#include <Phase1/Phase1BreakoutRetest.mqh>

input string InpRunId = "phase2-demo-repair-executor-v1";
input bool InpDryRunOnly = false;
input bool InpBrokerActionAllowed = false;
input string InpCandidate = "symbol_normalized_round_retest_v0_repair_v1";
input string InpCandidateStatus = "REPAIRED_EXPERIMENTAL_DEMO_V1";
input string InpFamilyLifecycleStatus = "COST_SUSPENDED_CANONICAL";
input string InpTargetSymbol = "XAUUSD";
input string InpQualifiedSymbolsCsv = "XAUUSD,EURUSD,GBPUSD";
input string InpExpectedServerMarker = "Demo";
input string InpAllowedAccountLoginsCsv = "";
input string InpExperimentalAuthorizationToken = "";
input string InpRequiredExperimentalAuthorizationToken = "EXPERIMENTAL_DEMO_AUTHORIZED_REVIEW_ONLY";
input string InpCostSuspensionAcknowledgementToken = "";
input string InpRequiredCostSuspensionAcknowledgementToken = "I_ACKNOWLEDGE_COST_SUSPENDED_NON_CANONICAL_EXPERIMENT";
input string InpAuthorizedCandidatesCsv = "symbol_normalized_round_retest_v0_repair_v1,session_extreme_retest_v0_repair_v1";
input string InpAttachmentLogFileName = "phase2_demo_repair_executor_signal_log_v1.csv";
input string InpStartupLogFileName = "phase2_demo_repair_executor_startup_v1.csv";
input string InpOrderLogFileName = "phase2_demo_repair_executor_order_log_v1.csv";
input string InpKillSwitchFileName = "phase2_demo_repair_kill_switch.txt";
input bool InpTradeSessionGateEnabled = false;
input int InpTradeSessionStartHour = 0;
input int InpTradeSessionEndHour = 23;
input double InpFixedLot = 0.01;
input double InpEURUSDFixedLot = 0.01;
input double InpGBPUSDFixedLot = 0.01;
input int InpMaxOrdersPerDay = 0;
input int InpMaxAccountOrdersPerDay = 0;
input int InpMinSecondsBetweenOrders = 0;
input int InpMaxOpenPositionsPerInstance = 0;
input int InpDeviationPoints = 50;
input double InpMaxEstimatedCostR = 0.00;
input double InpMaxMeasuredSpreadPoints = 0.0;
input int InpDubaiUtcOffsetMinutes = 240;

CPhase1BreakoutRetestObserver g_breakout_observer;
datetime g_last_m5_bar_time = 0;
datetime g_last_order_submit_time = 0;
string g_order_day_key = "";
int g_orders_today = 0;

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

string BaseCandidateName(const string candidate)
{
   if(candidate == "symbol_normalized_round_retest_v0_repair_v1")
      return "symbol_normalized_round_retest_v0";
   if(candidate == "session_extreme_retest_v0_repair_v1")
      return "session_extreme_retest_v0";
   return candidate;
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

bool IsAllowedCandidate(const string candidate)
{
   return candidate == "symbol_normalized_round_retest_v0_repair_v1"
      || candidate == "session_extreme_retest_v0_repair_v1"
      || candidate == "breakout_retest"
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
   return BaseCandidateName(candidate) == "swing_breakout_retest_v0";
}

bool CandidateUsesSymbolNormalizedRoundObserver(const string candidate)
{
   return BaseCandidateName(candidate) == "symbol_normalized_round_retest_v0";
}

bool CandidateUsesRoundObserver(const string candidate)
{
   string base = BaseCandidateName(candidate);
   return base == "round_number_retest_v0" || CandidateUsesSymbolNormalizedRoundObserver(base);
}

bool CandidateUsesSessionExtremeObserver(const string candidate)
{
   return BaseCandidateName(candidate) == "session_extreme_retest_v0";
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
   if(candidate == "symbol_normalized_round_retest_v0_repair_v1")
      return "REPAIR_SYMBOL_NORMALIZED_ROUND_RETEST";
   if(candidate == "session_extreme_retest_v0_repair_v1")
      return "REPAIR_SESSION_EXTREME_RETEST";
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
   if(handle == INVALID_HANDLE)
      return false;
   string content = "";
   while(!FileIsEnding(handle))
      content += " " + FileReadString(handle);
   FileClose(handle);
   return ContainsText(content, "KILL");
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
   return "P2REPAIR_ORD_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + CompactDateKey();
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
   return magic >= 920000 && magic < 922000;
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
      "guard_reason"
   };
   return AppendCsvRow(InpOrderLogFileName, header);
}

int CandidateMagicOffset(const string candidate)
{
   if(candidate == "symbol_normalized_round_retest_v0_repair_v1")
      return 10;
   if(candidate == "session_extreme_retest_v0_repair_v1")
      return 20;
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
   return 9;
}

long InstanceMagic()
{
   return 921000 + CandidateMagicOffset(InpCandidate) * 10 + SymbolMagicOffset(_Symbol);
}

string InstanceComment()
{
   string candidate = InpCandidate;
   StringReplace(candidate, "symbol_normalized_round_retest_v0_repair_v1", "snr_fix");
   StringReplace(candidate, "session_extreme_retest_v0_repair_v1", "sess_fix");
   StringReplace(candidate, "symbol_normalized_round_retest_v0", "sn_round");
   StringReplace(candidate, "swing_breakout_retest_v0", "swing_br");
   StringReplace(candidate, "round_number_retest_v0", "round");
   StringReplace(candidate, "session_extreme_retest_v0", "sess_ext");
   StringReplace(candidate, "breakout_retest", "br");
   string comment = "P2REPAIR_" + candidate + "_" + _Symbol;
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

datetime DubaiTimeNow()
{
   return TimeGMT() + InpDubaiUtcOffsetMinutes * 60;
}

string RepairTimeBucket(const datetime value)
{
   MqlDateTime parts;
   TimeToStruct(value, parts);
   if(parts.hour >= 20 || parts.hour < 6)
      return "Night 20:00-05:59";
   if(parts.hour < 12)
      return "Morning 06:00-11:59";
   if(parts.hour < 16)
      return "Afternoon 12:00-15:59";
   return "Evening 16:00-19:59";
}

bool RepairFilterPass(const Phase1BreakoutRetestObservation &observation, string &guard_reason)
{
   string bucket = RepairTimeBucket(DubaiTimeNow());
   if(InpCandidate == "symbol_normalized_round_retest_v0_repair_v1")
   {
      if(_Symbol != "XAUUSD")
      {
         guard_reason = "repair_symbol_filter";
         return false;
      }
      if(observation.direction_text != "SHORT")
      {
         guard_reason = "repair_direction_filter";
         return false;
      }
      if(bucket != "Evening 16:00-19:59")
      {
         guard_reason = "repair_time_bucket_filter_" + bucket;
         return false;
      }
      return true;
   }
   if(InpCandidate == "session_extreme_retest_v0_repair_v1")
   {
      if(observation.direction_text != "SHORT")
      {
         guard_reason = "repair_direction_filter";
         return false;
      }
      if(_Symbol == "XAUUSD" && (bucket == "Afternoon 12:00-15:59" || bucket == "Evening 16:00-19:59"))
         return true;
      if(_Symbol == "EURUSD" && bucket == "Night 20:00-05:59")
         return true;
      guard_reason = "repair_cluster_filter_" + _Symbol + "_" + bucket;
      return false;
   }
   guard_reason = "pass";
   return true;
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
      guard_reason
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
   if(!ServerHourInTradeSession())
   {
      guard_reason = "server_hour_session_gate";
      return false;
   }
   if(!RepairFilterPass(observation, guard_reason))
      return false;
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
   if(InpMaxOpenPositionsPerInstance > 0 && CountOpenExposureForInstance() >= InpMaxOpenPositionsPerInstance)
   {
      guard_reason = "open_instance_exposure_exists";
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

   if(!EnsureAttachmentLogHeader() || !EnsureStartupLogHeader() || !EnsureOrderLogHeader())
      return INIT_FAILED;

   g_breakout_observer.Configure(CandidateUsesSwingObserver(InpCandidate));
   ResetDailyOrderCounterIfNeeded();
   WriteStartupRow("ATTACHED_DEMO_EXECUTOR_ENABLED");
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
      DoubleToString(observation.stop_distance_points, 2)
   };
   AppendCsvRow(InpAttachmentLogFileName, row);
   if(observation.would_signal)
      SendDemoMarketOrder(observation);
}
