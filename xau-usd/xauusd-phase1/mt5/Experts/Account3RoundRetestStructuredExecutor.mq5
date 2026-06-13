// Account 3 repair lane. Experimental demo only; not canonical Phase 2.
// EA-T2 / RDSTRUCT_V1: symbol-normalized round retest plus M15 structure filter.
#property strict
#property version   "1.000"
#property description "A3 round-retest guarded executor. Demo-only, dry-run by committed default."

input string InpRunId = "A3_RDSTRUCT_V1";
input bool InpDryRunOnly = true;
input bool InpBrokerActionAllowed = false;
input string InpTargetSymbol = "XAUUSD";
input string InpExpectedServerMarker = "Demo";
input string InpAllowedAccountLoginsCsv = "1033669";
input string InpKillSwitchFileName = "A3_KILL.txt";
input int InpMagicNumber = 933100;
input string InpOrderComment = "RDSTRUCT_V1";
input string InpSignalLogFileName = "a3_rdstruct_v1_signal_log.csv";
input string InpStartupLogFileName = "a3_rdstruct_v1_startup.csv";
input string InpOrderLogFileName = "a3_rdstruct_v1_order_log.csv";
input int InpM15StructureLookbackBars = 20;
input int InpSwingConfirmLeftBars = 4;
input int InpSwingConfirmRightBars = 4;
input int InpStreakLossCount = 3;
input int InpStreakWindowMinutes = 120;
input int InpDubaiUtcOffsetMinutes = 240;
input double InpDailyLossStopAed = -150.0;
input int InpMaxOpenPositionsPerMagic = 1;
input double InpMaxEstimatedCostR = 0.15;
input double InpCostWarnR = 0.20;
input double InpAbsoluteRejectCostR = 0.30;
input double InpMaxMeasuredSpreadPoints = 75.0;
input int InpMinSecondsBetweenOrders = 60;
input double InpFixedLot = 0.01;
input int InpDeviationPoints = 50;

datetime g_last_m5_bar_time = 0;
datetime g_last_order_submit_time = 0;
datetime g_streak_pause_until = 0;
datetime g_daily_pause_until = 0;
string g_mutex_claim_name = "";
datetime g_mutex_claim_bar_time = 0;

struct A3RoundRetestObservation
{
   bool would_signal;
   bool confirmation_valid;
   bool level_found;
   bool break_found;
   bool retest_valid;
   string stage;
   string reason_code;
   string direction_text;
   string level_kind;
   double level_price;
   double entry_price;
   double stop_loss;
   double take_profit;
   double stop_distance_points;
   int break_shift;
};

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

struct A3StructureState
{
   bool confirmed;
   int swing_bar_index;
   datetime swing_bar_time;
   string break_direction;
   double swing_level;
   double break_close;
   double distance_from_level_points;
};

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

string CsvEscape(string value)
{
   StringReplace(value, "\"", "\"\"");
   if(StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0 || StringFind(value, "\r") >= 0)
      return "\"" + value + "\"";
   return value;
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
      "account_login",
      "symbol",
      "magic",
      "comment",
      "allowed_account_logins",
      "dry_run",
      "broker_action_allowed",
      "fixed_lot",
      "max_open_positions_per_magic",
      "max_estimated_cost_R",
      "cost_warn_R",
      "absolute_reject_cost_R",
      "max_measured_spread_points",
      "min_seconds_between_orders",
      "kill_switch_file",
      "startup_status"
   };
   return AppendCsvRow(InpStartupLogFileName, header);
}

bool EnsureSignalLogHeader()
{
   if(FileIsExist(InpSignalLogFileName))
      return true;
   string header[] = {
      "timestamp_broker",
      "timestamp_utc",
      "timestamp_local",
      "run_id",
      "account_server",
      "account_login",
      "symbol",
      "magic",
      "comment",
      "m5_bar_time",
      "bid",
      "ask",
      "spread_points",
      "stage",
      "direction",
      "would_signal",
      "reason_code",
      "guard_reason",
      "guard_pass",
      "level_kind",
      "level_price",
      "entry_price",
      "stop_loss",
      "take_profit",
      "stop_distance_points",
      "structure_confirmed",
      "structure_swing_bar_index",
      "structure_swing_time",
      "structure_break_direction",
      "structure_level",
      "structure_break_close",
      "structure_distance_from_level_points",
      "estimated_cost_R",
      "cost_warn",
      "open_positions_for_magic",
      "streak_sl_count",
      "streak_pause_until",
      "daily_realized_pnl_aed",
      "daily_pause_until",
      "mutex_name",
      "confluence_families",
      "confluence_count",
      "dry_run",
      "broker_action_allowed"
   };
   return AppendCsvRow(InpSignalLogFileName, header);
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
      "magic",
      "comment",
      "action",
      "direction",
      "volume",
      "request_price",
      "sl",
      "tp",
      "retcode",
      "retcode_description",
      "order_ticket",
      "deal_ticket",
      "result_price",
      "result_volume",
      "spread_points",
      "estimated_cost_R",
      "stop_distance_points",
      "reason_code",
      "guard_reason",
      "mutex_name"
   };
   return AppendCsvRow(InpOrderLogFileName, header);
}

bool WriteStartupRow(const string status_text)
{
   string row[] = {
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)),
      _Symbol,
      IntegerToString(InpMagicNumber),
      InpOrderComment,
      InpAllowedAccountLoginsCsv,
      BoolText(InpDryRunOnly),
      BoolText(InpBrokerActionAllowed),
      DoubleToString(InpFixedLot, 2),
      IntegerToString(InpMaxOpenPositionsPerMagic),
      DoubleToString(InpMaxEstimatedCostR, 4),
      DoubleToString(InpCostWarnR, 4),
      DoubleToString(InpAbsoluteRejectCostR, 4),
      DoubleToString(InpMaxMeasuredSpreadPoints, 2),
      IntegerToString(InpMinSecondsBetweenOrders),
      InpKillSwitchFileName,
      status_text
   };
   return AppendCsvRow(InpStartupLogFileName, row);
}

void ResetObservation(A3RoundRetestObservation &observation)
{
   observation.would_signal = false;
   observation.confirmation_valid = false;
   observation.level_found = false;
   observation.break_found = false;
   observation.retest_valid = false;
   observation.stage = "INIT";
   observation.reason_code = "";
   observation.direction_text = "NONE";
   observation.level_kind = "none";
   observation.level_price = 0.0;
   observation.entry_price = 0.0;
   observation.stop_loss = 0.0;
   observation.take_profit = 0.0;
   observation.stop_distance_points = 0.0;
   observation.break_shift = -1;
}

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

int DemoCandidateLevels(
   const string symbol_name,
   const double point,
   const double break_close,
   const bool is_long,
   DemoRetestCandidate &levels[]
)
{
   int count = 0;
   AddRoundLevels(symbol_name, point, break_close, is_long, true, levels, count);
   return count;
}

bool EvaluateSymbolNormalizedRoundRetest(
   const string symbol_name,
   const double point,
   A3RoundRetestObservation &observation
)
{
   ResetObservation(observation);
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
      if(break_atr <= 0.0 || break_close <= 0.0)
         continue;

      DemoRetestCandidate levels[3];
      for(int init = 0; init < 3; init++)
         ResetDemoCandidate(levels[init]);
      int level_count = DemoCandidateLevels(symbol_name, point, break_close, is_long, levels);
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
      observation.reason_code = "no_" + direction + "_symbol_normalized_round_retest_v0_candidate";
      return false;
   }

   observation.break_found = true;
   observation.retest_valid = true;
   observation.stage = "WOULD_SIGNAL";
   observation.reason_code = is_long ? "SYMBOL_NORMALIZED_ROUND_RETEST_LONG_DRY_RUN" : "SYMBOL_NORMALIZED_ROUND_RETEST_SHORT_DRY_RUN";
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

void ResetStructureState(A3StructureState &state)
{
   state.confirmed = false;
   state.swing_bar_index = -1;
   state.swing_bar_time = 0;
   state.break_direction = "NONE";
   state.swing_level = 0.0;
   state.break_close = 0.0;
   state.distance_from_level_points = 0.0;
}

bool ConfirmedM15SwingLevel(
   const bool is_long,
   const int start_shift,
   int &swing_shift,
   datetime &swing_time,
   double &swing_level
)
{
   int first_shift = MathMax(start_shift, InpSwingConfirmLeftBars + InpSwingConfirmRightBars + 1);
   for(int shift = first_shift; shift < start_shift + 80; shift++)
   {
      double price = is_long ? iHigh(_Symbol, PERIOD_M15, shift) : iLow(_Symbol, PERIOD_M15, shift);
      if(price <= 0.0)
         continue;
      bool confirmed = true;
      for(int offset = 1; offset <= InpSwingConfirmLeftBars; offset++)
      {
         double newer = is_long ? iHigh(_Symbol, PERIOD_M15, shift - offset) : iLow(_Symbol, PERIOD_M15, shift - offset);
         if(newer <= 0.0)
         {
            confirmed = false;
            break;
         }
         if(is_long && price <= newer)
            confirmed = false;
         if(!is_long && price >= newer)
            confirmed = false;
      }
      for(int offset = 1; offset <= InpSwingConfirmRightBars; offset++)
      {
         double older = is_long ? iHigh(_Symbol, PERIOD_M15, shift + offset) : iLow(_Symbol, PERIOD_M15, shift + offset);
         if(older <= 0.0)
         {
            confirmed = false;
            break;
         }
         if(is_long && price <= older)
            confirmed = false;
         if(!is_long && price >= older)
            confirmed = false;
      }
      if(confirmed)
      {
         swing_shift = shift;
         swing_time = iTime(_Symbol, PERIOD_M15, shift);
         swing_level = price;
         return true;
      }
   }
   return false;
}

bool StructuralConfirmation(const A3RoundRetestObservation &observation, A3StructureState &state)
{
   ResetStructureState(state);
   bool is_long = observation.direction_text == "LONG";
   bool is_short = observation.direction_text == "SHORT";
   if(!is_long && !is_short)
      return false;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point <= 0.0 || Bars(_Symbol, PERIOD_M15) < 120)
      return false;
   state.break_direction = is_long ? "LONG" : "SHORT";
   for(int break_shift = 1; break_shift <= InpM15StructureLookbackBars; break_shift++)
   {
      int swing_shift = -1;
      datetime swing_time = 0;
      double swing_level = 0.0;
      if(!ConfirmedM15SwingLevel(is_long, break_shift + InpSwingConfirmRightBars, swing_shift, swing_time, swing_level))
         continue;
      double break_close = iClose(_Symbol, PERIOD_M15, break_shift);
      if(break_close <= 0.0)
         continue;
      double distance_points = is_long ? (break_close - swing_level) / point : (swing_level - break_close) / point;
      if(distance_points <= 0.0)
         continue;
      state.confirmed = true;
      state.swing_bar_index = swing_shift;
      state.swing_bar_time = swing_time;
      state.swing_level = swing_level;
      state.break_close = break_close;
      state.distance_from_level_points = distance_points;
      return true;
   }
   return false;
}

double CurrentSpreadPoints()
{
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point <= 0.0)
      return 0.0;
   return (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / point;
}

double EstimatedCostRForObservation(const A3RoundRetestObservation &observation, const double spread_points)
{
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double risk_price = MathAbs(observation.entry_price - observation.stop_loss);
   if(point <= 0.0 || risk_price <= 0.0)
      return 0.0;
   return spread_points * point / risk_price;
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

bool AccountLoginWhitelisted()
{
   return CsvContainsTextToken(InpAllowedAccountLoginsCsv, IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)));
}

bool ScopeLocksPass(string &guard_reason)
{
   if(_Symbol != "XAUUSD" || InpTargetSymbol != "XAUUSD")
   {
      guard_reason = "SCOPE_LOCK_BLOCK";
      return false;
   }
   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
   {
      guard_reason = "SCOPE_LOCK_BLOCK";
      return false;
   }
   if(!AccountLoginWhitelisted())
   {
      guard_reason = "SCOPE_LOCK_BLOCK";
      return false;
   }
   if(KillSwitchActive())
   {
      guard_reason = "SCOPE_LOCK_BLOCK";
      return false;
   }
   guard_reason = "PASS";
   return true;
}

datetime NextFourHourBoundary(const datetime value)
{
   long seconds = (long)value;
   long block = 4 * 60 * 60;
   return (datetime)(seconds + (block - (seconds % block)));
}

datetime DubaiNow()
{
   return TimeGMT() + InpDubaiUtcOffsetMinutes * 60;
}

datetime DubaiDayStartGmt()
{
   MqlDateTime parts;
   TimeToStruct(DubaiNow(), parts);
   parts.hour = 0;
   parts.min = 0;
   parts.sec = 0;
   return StructToTime(parts) - InpDubaiUtcOffsetMinutes * 60;
}

datetime NextDubaiDayStartGmt()
{
   return DubaiDayStartGmt() + 24 * 60 * 60;
}

int RefreshStreakPause()
{
   datetime now = TimeCurrent();
   if(g_streak_pause_until > now)
      return InpStreakLossCount;
   int consecutive_sl = 0;
   datetime from_time = now - InpStreakWindowMinutes * 60;
   if(!HistorySelect(from_time, now))
      return 0;
   for(int index = HistoryDealsTotal() - 1; index >= 0; index--)
   {
      ulong deal = HistoryDealGetTicket(index);
      if(deal == 0)
         continue;
      if((int)HistoryDealGetInteger(deal, DEAL_MAGIC) != InpMagicNumber)
         continue;
      if(HistoryDealGetString(deal, DEAL_SYMBOL) != _Symbol)
         continue;
      if((ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal, DEAL_ENTRY) != DEAL_ENTRY_OUT)
         continue;
      long reason = HistoryDealGetInteger(deal, DEAL_REASON);
      if(reason == DEAL_REASON_SL)
      {
         consecutive_sl++;
         if(consecutive_sl >= InpStreakLossCount)
         {
            g_streak_pause_until = NextFourHourBoundary(now);
            return consecutive_sl;
         }
         continue;
      }
      break;
   }
   return consecutive_sl;
}

double OwnMagicRealizedPnlSince(const datetime from_time)
{
   double pnl = 0.0;
   if(!HistorySelect(from_time, TimeCurrent()))
      return pnl;
   for(int index = 0; index < HistoryDealsTotal(); index++)
   {
      ulong deal = HistoryDealGetTicket(index);
      if(deal == 0)
         continue;
      if((int)HistoryDealGetInteger(deal, DEAL_MAGIC) != InpMagicNumber)
         continue;
      if(HistoryDealGetString(deal, DEAL_SYMBOL) != _Symbol)
         continue;
      if((ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal, DEAL_ENTRY) != DEAL_ENTRY_OUT)
         continue;
      pnl += HistoryDealGetDouble(deal, DEAL_PROFIT);
      pnl += HistoryDealGetDouble(deal, DEAL_SWAP);
      pnl += HistoryDealGetDouble(deal, DEAL_COMMISSION);
   }
   return pnl;
}

double RefreshDailyPause()
{
   datetime now = TimeCurrent();
   double pnl = OwnMagicRealizedPnlSince(DubaiDayStartGmt());
   if(g_daily_pause_until > now)
      return pnl;
   if(pnl <= InpDailyLossStopAed)
      g_daily_pause_until = NextDubaiDayStartGmt();
   return pnl;
}

int CountOpenPositionsForMagic()
{
   int count = 0;
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && (int)PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
         count++;
   }
   for(int index = 0; index < OrdersTotal(); index++)
   {
      ulong ticket = OrderGetTicket(index);
      if(ticket == 0)
         continue;
      if(!OrderSelect(ticket))
         continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol && (int)OrderGetInteger(ORDER_MAGIC) == InpMagicNumber)
         count++;
   }
   return count;
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
   return (datetime)((long)(TimeCurrent() / 300) * 300);
}

string MutexDirectionToken(const string direction_text)
{
   if(direction_text == "LONG")
      return "BUY";
   if(direction_text == "SHORT")
      return "SELL";
   return "NONE";
}

string MutexNameForObservation(const A3RoundRetestObservation &observation)
{
   string direction = MutexDirectionToken(observation.direction_text);
   datetime bar_time = CurrentM5BarStart();
   if(direction == "NONE" || bar_time <= 0)
      return "";
   return "FAMMUX_RDSTRUCT_XAUUSD_" + direction + "_" + CompactDateTimeForGlobalVariable(bar_time);
}

string ConfluenceFamiliesForSignal(const A3RoundRetestObservation &observation)
{
   if(!observation.would_signal)
      return "";
   return "ROUND";
}

int ConfluenceCountForSignal(const A3RoundRetestObservation &observation)
{
   if(!observation.would_signal)
      return 0;
   return 1;
}

bool EnsureMutexSlot(const string mutex_name)
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
   Print("Could not create A3 mutex ", mutex_name, " error=", GetLastError());
   return false;
}

void ExpireMutexClaim()
{
   if(g_mutex_claim_name == "")
      return;
   if(TimeCurrent() < g_mutex_claim_bar_time + 300)
      return;
   if(GlobalVariableCheck(g_mutex_claim_name))
   {
      double owner = GlobalVariableGet(g_mutex_claim_name);
      if((int)owner == InpMagicNumber)
         GlobalVariableDel(g_mutex_claim_name);
   }
   g_mutex_claim_name = "";
   g_mutex_claim_bar_time = 0;
}

bool ClaimMutexBeforeOrder(const A3RoundRetestObservation &observation, string &mutex_name)
{
   ExpireMutexClaim();
   mutex_name = MutexNameForObservation(observation);
   if(!EnsureMutexSlot(mutex_name))
      return false;
   if(GlobalVariableSetOnCondition(mutex_name, InpMagicNumber, 0))
   {
      g_mutex_claim_name = mutex_name;
      g_mutex_claim_bar_time = CurrentM5BarStart();
      return true;
   }
   return false;
}

bool RunFamilyMutexNamespaceSelfTest(string &status_text)
{
   string test_name = "FAMMUX_SELFTEST_RDSTRUCT_" + IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + CompactDateTimeForGlobalVariable(TimeGMT());
   if(GlobalVariableCheck(test_name))
      GlobalVariableDel(test_name);
   bool created = EnsureMutexSlot(test_name);
   bool claimed = false;
   bool deleted = false;
   double stored_value = 0.0;
   if(created)
   {
      ResetLastError();
      claimed = GlobalVariableSetOnCondition(test_name, (double)InpMagicNumber, 0.0);
      if(GlobalVariableCheck(test_name))
         stored_value = GlobalVariableGet(test_name);
      deleted = GlobalVariableDel(test_name);
   }
   bool passed = created && claimed && ((int)stored_value == InpMagicNumber) && deleted;
   status_text = passed
      ? "GV_MUTEX_NAMESPACE_SELF_TEST_PASS name=" + test_name
      : "GV_MUTEX_NAMESPACE_SELF_TEST_FAIL name=" + test_name
         + " created=" + BoolText(created)
         + " claimed=" + BoolText(claimed)
         + " deleted=" + BoolText(deleted);
   return passed;
}

bool TradingGuardsPass(
   const A3RoundRetestObservation &observation,
   const A3StructureState &structure_state,
   const double spread_points,
   const double estimated_cost_r,
   string &guard_reason,
   int &streak_sl_count,
   double &daily_pnl
)
{
   if(!observation.would_signal)
   {
      guard_reason = "NO_SIGNAL";
      return false;
   }
   if(!structure_state.confirmed)
   {
      guard_reason = "STRUCT_FILTER_BLOCK";
      return false;
   }
   streak_sl_count = RefreshStreakPause();
   if(g_streak_pause_until > TimeCurrent())
   {
      guard_reason = "STREAK_PAUSE";
      return false;
   }
   daily_pnl = RefreshDailyPause();
   if(g_daily_pause_until > TimeCurrent())
   {
      guard_reason = "DAILY_STOP_PAUSE";
      return false;
   }
   if(CountOpenPositionsForMagic() >= InpMaxOpenPositionsPerMagic)
   {
      guard_reason = "MAGIC_POSITION_CAP_BLOCK";
      return false;
   }
   if(spread_points > InpMaxMeasuredSpreadPoints)
   {
      guard_reason = "SPREAD_CAP_BLOCK";
      return false;
   }
   if(estimated_cost_r > InpAbsoluteRejectCostR || estimated_cost_r > InpMaxEstimatedCostR)
   {
      guard_reason = "COST_R_CAP_BLOCK";
      return false;
   }
   if(InpMinSecondsBetweenOrders > 0 && g_last_order_submit_time > 0 && TimeCurrent() - g_last_order_submit_time < InpMinSecondsBetweenOrders)
   {
      guard_reason = "MIN_SECONDS_BETWEEN_ORDERS";
      return false;
   }
   if(!ScopeLocksPass(guard_reason))
      return false;
   guard_reason = "PASS";
   return true;
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
   return NormalizeDouble(volume, 2);
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

void WriteOrderLogRow(
   const string action,
   const A3RoundRetestObservation &observation,
   const double volume,
   const double request_price,
   const double sl,
   const double tp,
   const MqlTradeResult &result,
   const string guard_reason,
   const string mutex_name,
   const double spread_points,
   const double estimated_cost_r,
   const double stop_distance_points
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
      IntegerToString(InpMagicNumber),
      InpOrderComment,
      action,
      observation.direction_text,
      DoubleToString(volume, 2),
      DoubleToString(request_price, digits),
      DoubleToString(sl, digits),
      DoubleToString(tp, digits),
      IntegerToString((int)result.retcode),
      result.comment,
      IntegerToString((int)result.order),
      IntegerToString((int)result.deal),
      DoubleToString(result.price, digits),
      DoubleToString(result.volume, 2),
      DoubleToString(spread_points, 2),
      DoubleToString(estimated_cost_r, 4),
      DoubleToString(stop_distance_points, 2),
      observation.reason_code,
      guard_reason,
      mutex_name
   };
   AppendCsvRow(InpOrderLogFileName, row);
}

bool SendMarketOrder(const A3RoundRetestObservation &observation, const double spread_points, const double estimated_cost_r)
{
   MqlTradeResult result;
   ZeroMemory(result);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   bool is_long = observation.direction_text == "LONG";
   double price = is_long ? ask : bid;
   double signal_risk = MathAbs(observation.entry_price - observation.stop_loss);
   if(point <= 0.0 || signal_risk <= 0.0 || price <= 0.0)
   {
      WriteOrderLogRow("GUARD_BLOCK", observation, 0.0, price, 0.0, 0.0, result, "INVALID_PRICE_OR_RISK", "", spread_points, estimated_cost_r, observation.stop_distance_points);
      return false;
   }
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double sl = NormalizeDouble(is_long ? price - signal_risk : price + signal_risk, digits);
   double tp = NormalizeDouble(is_long ? price + 1.50 * signal_risk : price - 1.50 * signal_risk, digits);
   price = NormalizeDouble(price, digits);
   double volume = NormalizeVolumeForSymbol(InpFixedLot);
   if(volume <= 0.0)
   {
      WriteOrderLogRow("GUARD_BLOCK", observation, 0.0, price, sl, tp, result, "INVALID_VOLUME", "", spread_points, estimated_cost_r, observation.stop_distance_points);
      return false;
   }
   string mutex_name = "";
   if(!ClaimMutexBeforeOrder(observation, mutex_name))
   {
      WriteOrderLogRow("GUARD_BLOCK", observation, 0.0, price, sl, tp, result, "MUTEX_CLAIMED_ELSEWHERE", mutex_name, spread_points, estimated_cost_r, observation.stop_distance_points);
      return false;
   }

   MqlTradeRequest request;
   ZeroMemory(request);
   request.action = TRADE_ACTION_DEAL;
   request.symbol = _Symbol;
   request.magic = InpMagicNumber;
   request.volume = volume;
   request.type = is_long ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   request.price = price;
   request.sl = sl;
   request.tp = tp;
   request.deviation = InpDeviationPoints;
   request.type_filling = FillPolicy();
   request.type_time = ORDER_TIME_GTC;
   request.comment = InpOrderComment;

   bool sent = OrderSend(request, result);
   string action = sent ? "ORDER_SEND_OK" : "ORDER_SEND_FAIL";
   if(sent && (result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_PLACED || result.retcode == TRADE_RETCODE_DONE_PARTIAL))
      g_last_order_submit_time = TimeCurrent();
   WriteOrderLogRow(action, observation, volume, price, sl, tp, result, "PASS", mutex_name, spread_points, estimated_cost_r, observation.stop_distance_points);
   return sent;
}

void WriteSignalRow(
   const A3RoundRetestObservation &observation,
   const A3StructureState &structure_state,
   const double spread_points,
   const double estimated_cost_r,
   const string guard_reason,
   const bool guard_pass,
   const int streak_sl_count,
   const double daily_pnl,
   const string mutex_name
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
      IntegerToString(InpMagicNumber),
      InpOrderComment,
      TimeToString(CurrentM5BarStart(), TIME_DATE | TIME_SECONDS),
      DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_BID), digits),
      DoubleToString(SymbolInfoDouble(_Symbol, SYMBOL_ASK), digits),
      DoubleToString(spread_points, 2),
      observation.stage,
      observation.direction_text,
      BoolText(observation.would_signal),
      observation.reason_code,
      guard_reason,
      BoolText(guard_pass),
      observation.level_kind,
      DoubleToString(observation.level_price, digits),
      DoubleToString(observation.entry_price, digits),
      DoubleToString(observation.stop_loss, digits),
      DoubleToString(observation.take_profit, digits),
      DoubleToString(observation.stop_distance_points, 2),
      BoolText(structure_state.confirmed),
      IntegerToString(structure_state.swing_bar_index),
      TimeToString(structure_state.swing_bar_time, TIME_DATE | TIME_SECONDS),
      structure_state.break_direction,
      DoubleToString(structure_state.swing_level, digits),
      DoubleToString(structure_state.break_close, digits),
      DoubleToString(structure_state.distance_from_level_points, 2),
      DoubleToString(estimated_cost_r, 4),
      estimated_cost_r > InpCostWarnR ? "COST_WARN" : "",
      IntegerToString(CountOpenPositionsForMagic()),
      IntegerToString(streak_sl_count),
      TimeToString(g_streak_pause_until, TIME_DATE | TIME_SECONDS),
      DoubleToString(daily_pnl, 2),
      TimeToString(g_daily_pause_until, TIME_DATE | TIME_SECONDS),
      mutex_name,
      ConfluenceFamiliesForSignal(observation),
      IntegerToString(ConfluenceCountForSignal(observation)),
      BoolText(InpDryRunOnly),
      BoolText(InpBrokerActionAllowed)
   };
   AppendCsvRow(InpSignalLogFileName, row);
}

int OnInit()
{
   if(!EnsureStartupLogHeader() || !EnsureSignalLogHeader() || !EnsureOrderLogHeader())
      return INIT_FAILED;
   string scope_reason = "";
   if(!ScopeLocksPass(scope_reason))
   {
      WriteStartupRow(scope_reason);
      return INIT_FAILED;
   }
   if(InpMagicNumber < 933100 || InpMagicNumber > 933199)
   {
      WriteStartupRow("SCOPE_LOCK_BLOCK");
      return INIT_FAILED;
   }
   string gv_mutex_self_test_status = "";
   if(!RunFamilyMutexNamespaceSelfTest(gv_mutex_self_test_status))
   {
      WriteStartupRow(gv_mutex_self_test_status);
      return INIT_FAILED;
   }
   WriteStartupRow(gv_mutex_self_test_status);
   WriteStartupRow("ATTACHED_A3_RDSTRUCT_V1");
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ExpireMutexClaim();
   WriteStartupRow("REMOVED_REASON_" + IntegerToString(reason));
}

void OnTimer()
{
   ExpireMutexClaim();
   datetime m5_bar_time = iTime(_Symbol, PERIOD_M5, 0);
   if(m5_bar_time <= 0 || m5_bar_time == g_last_m5_bar_time)
      return;
   g_last_m5_bar_time = m5_bar_time;

   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   A3RoundRetestObservation observation;
   EvaluateSymbolNormalizedRoundRetest(_Symbol, point, observation);
   A3StructureState structure_state;
   StructuralConfirmation(observation, structure_state);
   double spread_points = CurrentSpreadPoints();
   double estimated_cost_r = EstimatedCostRForObservation(observation, spread_points);
   int streak_sl_count = 0;
   double daily_pnl = RefreshDailyPause();
   string guard_reason = observation.would_signal ? "PASS" : "NO_SIGNAL";
   bool guard_pass = TradingGuardsPass(observation, structure_state, spread_points, estimated_cost_r, guard_reason, streak_sl_count, daily_pnl);
   string mutex_name = observation.would_signal ? MutexNameForObservation(observation) : "";
   if(guard_pass && (InpDryRunOnly || !InpBrokerActionAllowed))
   {
      guard_pass = false;
      guard_reason = "ARMING_DISABLED";
   }
   WriteSignalRow(observation, structure_state, spread_points, estimated_cost_r, guard_reason, guard_pass, streak_sl_count, daily_pnl, mutex_name);
   if(guard_pass)
      SendMarketOrder(observation, spread_points, estimated_cost_r);
}
