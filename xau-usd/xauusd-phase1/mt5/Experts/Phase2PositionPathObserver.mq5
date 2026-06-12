#property strict
#property version   "1.000"
#property description "Position path observer. Telemetry only; no broker actions or order placement."

input string InpRunId = "phase2-position-path-observer-v0.1";
input bool InpDryRunOnly = true;
input string InpExpectedServerMarker = "Demo";
input int InpSnapshotSeconds = 10;
input int InpDubaiUtcOffsetMinutes = 240;
input string InpSnapshotFilePrefix = "position_path_log";
input string InpSummaryFileName = "position_path_summary.csv";
input string InpStartupFileName = "position_path_observer_startup.csv";

const bool BROKER_ACTION_ALLOWED = false;
#define MAX_TRACKED_POSITIONS 512
#define MAX_SYMBOL_CONTEXTS 64

struct PositionPathState
{
   ulong ticket;
   long magic;
   string candidate;
   string comment;
   string symbol_name;
   string direction;
   double volume;
   datetime entry_time_broker;
   double entry_price;
   double sl_initial;
   double tp_initial;
   double sl_last;
   double tp_last;
   double initial_stop_points;
   datetime first_snapshot_utc;
   datetime last_snapshot_utc;
   int snapshots_count;
   bool observed_in_evening;
   bool active;
};

struct SymbolIndicatorContext
{
   string symbol_name;
   int m15_ema20_handle;
   int h1_ema20_handle;
   int d1_ema20_handle;
   int d1_ema50_handle;
   bool ready;
};

PositionPathState g_positions[MAX_TRACKED_POSITIONS];
SymbolIndicatorContext g_contexts[MAX_SYMBOL_CONTEXTS];
int g_context_count = 0;

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

datetime DubaiNow()
{
   return TimeGMT() + InpDubaiUtcOffsetMinutes * 60;
}

string DateToken(const datetime value)
{
   MqlDateTime parts;
   TimeToStruct(value, parts);
   return StringFormat("%04d%02d%02d", parts.year, parts.mon, parts.day);
}

string TimeBucketDubai(const datetime value)
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

string SnapshotFileName()
{
   return InpSnapshotFilePrefix + "_" + DateToken(DubaiNow()) + ".csv";
}

string DirectionFromPositionType(const long position_type)
{
   if(position_type == POSITION_TYPE_BUY)
      return "BUY";
   if(position_type == POSITION_TYPE_SELL)
      return "SELL";
   return "UNKNOWN";
}

string CandidateFromMagicAndComment(const long magic, const string comment)
{
   if(magic == 931000 || magic == 930101 || ContainsText(comment, "P2WEAKNESS"))
      return "p2weakness_br_v1";
   if(magic >= 930000 && magic < 930100)
      return "WR50_BreakoutEvening_v0";
   if(magic >= 930100 && magic < 930200)
      return "WR50_BreakoutQuality_v0";
   if(magic >= 930200 && magic < 930300)
      return "WR50_Exit1R_v0";
   if(magic >= 930300 && magic < 930400)
      return "WR50_BreakoutWideStop_WST12";
   if(magic >= 930400 && magic < 930500)
      return "WR50_BreakoutWideStop_WST15";
   if(magic >= 932100 && magic < 932200)
      return "W1D1_momentum_continuation";
   if(magic >= 921100 && magic < 921200)
      return "symbol_normalized_round_retest_v0_repair_v1";
   if(magic >= 921200 && magic < 921300)
      return "session_extreme_retest_v0_repair_v1";
   if(magic >= 920100 && magic < 920200)
      return "breakout_retest";
   if(magic >= 920200 && magic < 920300)
      return "swing_breakout_retest_v0";
   if(magic >= 920300 && magic < 920400)
      return "symbol_normalized_round_retest_v0";
   if(magic >= 920400 && magic < 920500)
      return "round_number_retest_v0";
   if(magic >= 920500 && magic < 920600)
      return "session_extreme_retest_v0";
   if(ContainsText(comment, "P2DEMO_br"))
      return "breakout_retest";
   if(ContainsText(comment, "P2DEMO_swing"))
      return "swing_breakout_retest_v0";
   if(ContainsText(comment, "P2DEMO_sn_round"))
      return "symbol_normalized_round_retest_v0";
   if(ContainsText(comment, "P2DEMO_round"))
      return "round_number_retest_v0";
   if(ContainsText(comment, "P2DEMO_sess_ext"))
      return "session_extreme_retest_v0";
   if(ContainsText(comment, "P2REPAIR_snr"))
      return "symbol_normalized_round_retest_v0_repair_v1";
   if(ContainsText(comment, "P2REPAIR_sess"))
      return "session_extreme_retest_v0_repair_v1";
   if(ContainsText(comment, "WR50"))
      return "WR50_unknown";
   return "unknown_magic_" + IntegerToString(magic);
}

int FindPositionStateIndex(const ulong ticket)
{
   for(int index = 0; index < MAX_TRACKED_POSITIONS; index++)
   {
      if(g_positions[index].active && g_positions[index].ticket == ticket)
         return index;
   }
   return -1;
}

int AllocatePositionStateIndex()
{
   for(int index = 0; index < MAX_TRACKED_POSITIONS; index++)
   {
      if(!g_positions[index].active)
         return index;
   }
   return -1;
}

bool TicketCurrentlyOpen(const ulong ticket)
{
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong current_ticket = PositionGetTicket(index);
      if(current_ticket == ticket)
         return true;
   }
   return false;
}

int FindSymbolContext(const string symbol_name)
{
   for(int index = 0; index < g_context_count; index++)
   {
      if(g_contexts[index].symbol_name == symbol_name)
         return index;
   }
   return -1;
}

int EnsureSymbolContext(const string symbol_name)
{
   int existing = FindSymbolContext(symbol_name);
   if(existing >= 0)
      return existing;
   if(g_context_count >= MAX_SYMBOL_CONTEXTS)
      return -1;

   SymbolSelect(symbol_name, true);
   int index = g_context_count;
   g_contexts[index].symbol_name = symbol_name;
   g_contexts[index].m15_ema20_handle = iMA(symbol_name, PERIOD_M15, 20, 0, MODE_EMA, PRICE_CLOSE);
   g_contexts[index].h1_ema20_handle = iMA(symbol_name, PERIOD_H1, 20, 0, MODE_EMA, PRICE_CLOSE);
   g_contexts[index].d1_ema20_handle = iMA(symbol_name, PERIOD_D1, 20, 0, MODE_EMA, PRICE_CLOSE);
   g_contexts[index].d1_ema50_handle = iMA(symbol_name, PERIOD_D1, 50, 0, MODE_EMA, PRICE_CLOSE);
   g_contexts[index].ready = g_contexts[index].m15_ema20_handle != INVALID_HANDLE
      && g_contexts[index].h1_ema20_handle != INVALID_HANDLE
      && g_contexts[index].d1_ema20_handle != INVALID_HANDLE
      && g_contexts[index].d1_ema50_handle != INVALID_HANDLE;
   g_context_count++;
   return index;
}

void ReleaseSymbolContexts()
{
   for(int index = 0; index < g_context_count; index++)
   {
      if(g_contexts[index].m15_ema20_handle != INVALID_HANDLE)
         IndicatorRelease(g_contexts[index].m15_ema20_handle);
      if(g_contexts[index].h1_ema20_handle != INVALID_HANDLE)
         IndicatorRelease(g_contexts[index].h1_ema20_handle);
      if(g_contexts[index].d1_ema20_handle != INVALID_HANDLE)
         IndicatorRelease(g_contexts[index].d1_ema20_handle);
      if(g_contexts[index].d1_ema50_handle != INVALID_HANDLE)
         IndicatorRelease(g_contexts[index].d1_ema50_handle);
      g_contexts[index].ready = false;
   }
   g_context_count = 0;
}

bool SeriesReady(const string symbol_name, const ENUM_TIMEFRAMES timeframe, const int required_bars)
{
   long synchronized = 0;
   if(!SeriesInfoInteger(symbol_name, timeframe, SERIES_SYNCHRONIZED, synchronized))
      return false;
   if(synchronized == 0)
      return false;
   return Bars(symbol_name, timeframe) >= required_bars;
}

bool CopyEmaValue(const int handle, const int shift, double &value)
{
   value = 0.0;
   if(handle == INVALID_HANDLE)
      return false;
   if(BarsCalculated(handle) <= shift)
      return false;
   double buffer[];
   ArraySetAsSeries(buffer, true);
   int copied = CopyBuffer(handle, 0, shift, 1, buffer);
   if(copied != 1)
      return false;
   value = buffer[0];
   return value > 0.0;
}

bool EmaSlopePointsFromHandle(const int handle, const int lookback_bars, const double point, double &slope_points)
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

double AverageRangePrice(const string symbol_name, const ENUM_TIMEFRAMES timeframe, const int periods, const int start_shift)
{
   if(!SeriesReady(symbol_name, timeframe, start_shift + periods + 1))
      return 0.0;
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

string DailyBiasText(const string symbol_name, const int context_index, bool &bias_available)
{
   bias_available = false;
   if(context_index < 0 || !g_contexts[context_index].ready)
      return "UNKNOWN";
   if(!SeriesReady(symbol_name, PERIOD_D1, 60))
      return "UNKNOWN";
   double close_price = iClose(symbol_name, PERIOD_D1, 1);
   double ema20 = 0.0;
   double ema50 = 0.0;
   if(close_price <= 0.0
      || !CopyEmaValue(g_contexts[context_index].d1_ema20_handle, 1, ema20)
      || !CopyEmaValue(g_contexts[context_index].d1_ema50_handle, 1, ema50))
      return "UNKNOWN";
   bias_available = true;
   if(close_price > ema20 && ema20 > ema50)
      return "BULLISH";
   if(close_price < ema20 && ema20 < ema50)
      return "BEARISH";
   return "MIXED";
}

string AvailabilityText(const bool value)
{
   return value ? "OK" : "SLOPE_UNAVAILABLE";
}

string CsvEscape(string value)
{
   bool needs_quote = StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0;
   StringReplace(value, "\"", "\"\"");
   if(needs_quote)
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

bool EnsureSnapshotHeader(const string file_name)
{
   if(FileIsExist(file_name))
      return true;
   string header[] = {
      "ts_utc",
      "ts_broker",
      "ts_local",
      "ts_dubai",
      "time_bucket",
      "observed_in_evening",
      "run_id",
      "account_server",
      "account_login",
      "position_ticket",
      "magic",
      "candidate",
      "position_comment",
      "symbol",
      "direction",
      "volume",
      "entry_time_broker",
      "entry_price",
      "sl_current",
      "tp_current",
      "sl_initial",
      "tp_initial",
      "initial_stop_points",
      "bid",
      "ask",
      "spread_points",
      "price_current",
      "unrealized_pnl_aed",
      "unrealized_R",
      "distance_to_sl_points",
      "distance_to_tp_points",
      "atr14_m5_points",
      "m15_ema20_slope_points",
      "m15_ema20_slope_status",
      "h1_ema20_slope_points",
      "h1_ema20_slope_status",
      "d1_bias",
      "d1_bias_status",
      "open_positions_total",
      "same_symbol_same_dir_count",
      "account_equity",
      "account_floating_total",
      "broker_action_allowed",
      "row_type"
   };
   return AppendCsvRow(file_name, header);
}

bool EnsureSummaryHeader()
{
   if(FileIsExist(InpSummaryFileName))
      return true;
   string header[] = {
      "ts_utc",
      "ts_broker",
      "ts_local",
      "ts_dubai",
      "close_time_bucket",
      "observed_in_evening",
      "run_id",
      "position_ticket",
      "magic",
      "candidate",
      "position_comment",
      "symbol",
      "direction",
      "volume",
      "entry_time_broker",
      "exit_time_broker",
      "entry_price",
      "exit_price",
      "sl_initial",
      "tp_initial",
      "sl_last",
      "tp_last",
      "exit_reason",
      "realized_pnl_aed",
      "realized_R",
      "slippage_points",
      "snapshots_count",
      "first_snapshot_ts_utc",
      "last_snapshot_ts_utc",
      "broker_action_allowed"
   };
   return AppendCsvRow(InpSummaryFileName, header);
}

bool EnsureStartupHeader()
{
   if(FileIsExist(InpStartupFileName))
      return true;
   string header[] = {
      "ts_utc",
      "ts_broker",
      "ts_local",
      "ts_dubai",
      "run_id",
      "account_server",
      "account_login",
      "dry_run",
      "broker_action_allowed",
      "snapshot_seconds",
      "dubai_utc_offset_minutes",
      "startup_status"
   };
   return AppendCsvRow(InpStartupFileName, header);
}

bool WriteStartupRow(const string status_text)
{
   string row[] = {
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      TimeToString(DubaiNow(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)),
      BoolText(InpDryRunOnly),
      BoolText(BROKER_ACTION_ALLOWED),
      IntegerToString(InpSnapshotSeconds),
      IntegerToString(InpDubaiUtcOffsetMinutes),
      status_text
   };
   return AppendCsvRow(InpStartupFileName, row);
}

double CurrentPriceForDirection(const string symbol_name, const string direction)
{
   if(direction == "BUY")
      return SymbolInfoDouble(symbol_name, SYMBOL_BID);
   if(direction == "SELL")
      return SymbolInfoDouble(symbol_name, SYMBOL_ASK);
   return PositionGetDouble(POSITION_PRICE_CURRENT);
}

double DistanceToSlPoints(const string direction, const double current_price, const double sl, const double point)
{
   if(sl <= 0.0 || point <= 0.0 || current_price <= 0.0)
      return 0.0;
   if(direction == "BUY")
      return (current_price - sl) / point;
   if(direction == "SELL")
      return (sl - current_price) / point;
   return 0.0;
}

double DistanceToTpPoints(const string direction, const double current_price, const double tp, const double point)
{
   if(tp <= 0.0 || point <= 0.0 || current_price <= 0.0)
      return 0.0;
   if(direction == "BUY")
      return (tp - current_price) / point;
   if(direction == "SELL")
      return (current_price - tp) / point;
   return 0.0;
}

double InitialStopPointsForPosition(const string direction, const double entry_price, const double sl, const double point)
{
   if(point <= 0.0 || entry_price <= 0.0 || sl <= 0.0)
      return 0.0;
   if(direction == "BUY")
      return MathAbs(entry_price - sl) / point;
   if(direction == "SELL")
      return MathAbs(sl - entry_price) / point;
   return 0.0;
}

double UnrealizedR(const string direction, const double entry_price, const double current_price, const double initial_stop_points, const double point)
{
   if(point <= 0.0 || initial_stop_points <= 0.0 || entry_price <= 0.0 || current_price <= 0.0)
      return 0.0;
   double movement_points = direction == "BUY"
      ? (current_price - entry_price) / point
      : (entry_price - current_price) / point;
   return movement_points / initial_stop_points;
}

int SameSymbolSameDirectionCount(const string symbol_name, const string direction)
{
   int count = 0;
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      string other_symbol = PositionGetString(POSITION_SYMBOL);
      string other_direction = DirectionFromPositionType((long)PositionGetInteger(POSITION_TYPE));
      if(other_symbol == symbol_name && other_direction == direction)
         count++;
   }
   return count;
}

bool WriteSnapshotRow(const ulong ticket, const string row_type)
{
   if(!PositionSelectByTicket(ticket))
      return false;
   string file_name = SnapshotFileName();
   if(!EnsureSnapshotHeader(file_name))
      return false;

   string symbol_name = PositionGetString(POSITION_SYMBOL);
   SymbolSelect(symbol_name, true);
   long magic = (long)PositionGetInteger(POSITION_MAGIC);
   string comment = PositionGetString(POSITION_COMMENT);
   string candidate = CandidateFromMagicAndComment(magic, comment);
   string direction = DirectionFromPositionType((long)PositionGetInteger(POSITION_TYPE));
   double volume = PositionGetDouble(POSITION_VOLUME);
   datetime entry_time_broker = (datetime)PositionGetInteger(POSITION_TIME);
   double entry_price = PositionGetDouble(POSITION_PRICE_OPEN);
   double sl_current = PositionGetDouble(POSITION_SL);
   double tp_current = PositionGetDouble(POSITION_TP);
   double pnl = PositionGetDouble(POSITION_PROFIT);
   double point = SymbolInfoDouble(symbol_name, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(symbol_name, SYMBOL_DIGITS);
   double bid = SymbolInfoDouble(symbol_name, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol_name, SYMBOL_ASK);
   double spread_points = point > 0.0 ? (ask - bid) / point : 0.0;
   double price_current = CurrentPriceForDirection(symbol_name, direction);

   int state_index = FindPositionStateIndex(ticket);
   if(state_index < 0)
   {
      state_index = AllocatePositionStateIndex();
      if(state_index < 0)
         return false;
      g_positions[state_index].ticket = ticket;
      g_positions[state_index].magic = magic;
      g_positions[state_index].candidate = candidate;
      g_positions[state_index].comment = comment;
      g_positions[state_index].symbol_name = symbol_name;
      g_positions[state_index].direction = direction;
      g_positions[state_index].volume = volume;
      g_positions[state_index].entry_time_broker = entry_time_broker;
      g_positions[state_index].entry_price = entry_price;
      g_positions[state_index].sl_initial = sl_current;
      g_positions[state_index].tp_initial = tp_current;
      g_positions[state_index].sl_last = sl_current;
      g_positions[state_index].tp_last = tp_current;
      g_positions[state_index].initial_stop_points = InitialStopPointsForPosition(direction, entry_price, sl_current, point);
      g_positions[state_index].first_snapshot_utc = TimeGMT();
      g_positions[state_index].last_snapshot_utc = 0;
      g_positions[state_index].snapshots_count = 0;
      g_positions[state_index].observed_in_evening = false;
      g_positions[state_index].active = true;
   }

   datetime dubai_time = DubaiNow();
   string time_bucket = TimeBucketDubai(dubai_time);
   if(time_bucket == "Evening 16:00-19:59")
      g_positions[state_index].observed_in_evening = true;

   g_positions[state_index].sl_last = sl_current;
   g_positions[state_index].tp_last = tp_current;
   g_positions[state_index].last_snapshot_utc = TimeGMT();
   g_positions[state_index].snapshots_count++;

   int context_index = EnsureSymbolContext(symbol_name);
   double m15_slope = 0.0;
   double h1_slope = 0.0;
   bool m15_ok = context_index >= 0 && EmaSlopePointsFromHandle(g_contexts[context_index].m15_ema20_handle, 3, point, m15_slope);
   bool h1_ok = context_index >= 0 && EmaSlopePointsFromHandle(g_contexts[context_index].h1_ema20_handle, 3, point, h1_slope);
   bool d1_ok = false;
   string d1_bias = DailyBiasText(symbol_name, context_index, d1_ok);
   double atr14_m5_points = point > 0.0 ? AverageRangePrice(symbol_name, PERIOD_M5, 14, 1) / point : 0.0;
   double initial_stop_points = g_positions[state_index].initial_stop_points;
   double unrealized_r = UnrealizedR(direction, entry_price, price_current, initial_stop_points, point);

   string row[] = {
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      TimeToString(dubai_time, TIME_DATE | TIME_SECONDS),
      time_bucket,
      BoolText(g_positions[state_index].observed_in_evening),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)),
      IntegerToString((long)ticket),
      IntegerToString(magic),
      candidate,
      comment,
      symbol_name,
      direction,
      DoubleToString(volume, 2),
      TimeToString(entry_time_broker, TIME_DATE | TIME_SECONDS),
      DoubleToString(entry_price, digits),
      DoubleToString(sl_current, digits),
      DoubleToString(tp_current, digits),
      DoubleToString(g_positions[state_index].sl_initial, digits),
      DoubleToString(g_positions[state_index].tp_initial, digits),
      DoubleToString(initial_stop_points, 2),
      DoubleToString(bid, digits),
      DoubleToString(ask, digits),
      DoubleToString(spread_points, 2),
      DoubleToString(price_current, digits),
      DoubleToString(pnl, 2),
      DoubleToString(unrealized_r, 4),
      DoubleToString(DistanceToSlPoints(direction, price_current, sl_current, point), 2),
      DoubleToString(DistanceToTpPoints(direction, price_current, tp_current, point), 2),
      DoubleToString(atr14_m5_points, 2),
      DoubleToString(m15_slope, 2),
      AvailabilityText(m15_ok),
      DoubleToString(h1_slope, 2),
      AvailabilityText(h1_ok),
      d1_bias,
      d1_ok ? "OK" : "D1_BIAS_UNAVAILABLE",
      IntegerToString(PositionsTotal()),
      IntegerToString(SameSymbolSameDirectionCount(symbol_name, direction)),
      DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2),
      DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2),
      BoolText(BROKER_ACTION_ALLOWED),
      row_type
   };
   return AppendCsvRow(file_name, row);
}

string DealReasonText(const long reason)
{
   if(reason == DEAL_REASON_SL)
      return "SL";
   if(reason == DEAL_REASON_TP)
      return "TP";
   if(reason == DEAL_REASON_SO)
      return "STOP_OUT";
   if(reason == DEAL_REASON_CLIENT)
      return "CLIENT";
   if(reason == DEAL_REASON_MOBILE)
      return "MOBILE";
   if(reason == DEAL_REASON_WEB)
      return "WEB";
   if(reason == DEAL_REASON_EXPERT)
      return "EXPERT";
   return "OTHER";
}

bool FindCloseDeal(const PositionPathState &state, double &exit_price, datetime &exit_time, double &realized_pnl, string &exit_reason)
{
   exit_price = 0.0;
   exit_time = 0;
   realized_pnl = 0.0;
   exit_reason = "NOT_FOUND";
   datetime from_time = state.entry_time_broker - 86400;
   datetime to_time = TimeCurrent() + 86400;
   if(!HistorySelect(from_time, to_time))
      return false;

   bool found = false;
   int total = HistoryDealsTotal();
   for(int index = 0; index < total; index++)
   {
      ulong deal_ticket = HistoryDealGetTicket(index);
      if(deal_ticket == 0)
         continue;
      long position_id = (long)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID);
      if((ulong)position_id != state.ticket)
         continue;
      long entry = HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);
      if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_OUT_BY)
         continue;
      found = true;
      double profit = HistoryDealGetDouble(deal_ticket, DEAL_PROFIT);
      double swap = HistoryDealGetDouble(deal_ticket, DEAL_SWAP);
      double commission = HistoryDealGetDouble(deal_ticket, DEAL_COMMISSION);
      realized_pnl += profit + swap + commission;
      datetime deal_time = (datetime)HistoryDealGetInteger(deal_ticket, DEAL_TIME);
      if(deal_time >= exit_time)
      {
         exit_time = deal_time;
         exit_price = HistoryDealGetDouble(deal_ticket, DEAL_PRICE);
         exit_reason = DealReasonText(HistoryDealGetInteger(deal_ticket, DEAL_REASON));
      }
   }
   return found;
}

string SlippagePointsForExitText(const PositionPathState &state, const double exit_price, const string exit_reason)
{
   double point = SymbolInfoDouble(state.symbol_name, SYMBOL_POINT);
   if(point <= 0.0 || exit_price <= 0.0)
      return "NA";

   double reference = 0.0;
   if(exit_reason == "SL")
      reference = state.sl_last;
   else if(exit_reason == "TP")
      reference = state.tp_last;
   else
      return "NA";

   if(reference <= 0.0)
      return "NA";
   return DoubleToString(MathAbs(exit_price - reference) / point, 2);
}

bool WriteCloseDetectedSnapshot(
   const PositionPathState &state,
   const double exit_price,
   const double realized_pnl,
   const double realized_r
)
{
   string file_name = SnapshotFileName();
   if(!EnsureSnapshotHeader(file_name))
      return false;

   string symbol_name = state.symbol_name;
   SymbolSelect(symbol_name, true);
   double point = SymbolInfoDouble(symbol_name, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(symbol_name, SYMBOL_DIGITS);
   double bid = SymbolInfoDouble(symbol_name, SYMBOL_BID);
   double ask = SymbolInfoDouble(symbol_name, SYMBOL_ASK);
   double spread_points = point > 0.0 ? (ask - bid) / point : 0.0;
   int context_index = EnsureSymbolContext(symbol_name);
   double m15_slope = 0.0;
   double h1_slope = 0.0;
   bool m15_ok = context_index >= 0 && EmaSlopePointsFromHandle(g_contexts[context_index].m15_ema20_handle, 3, point, m15_slope);
   bool h1_ok = context_index >= 0 && EmaSlopePointsFromHandle(g_contexts[context_index].h1_ema20_handle, 3, point, h1_slope);
   bool d1_ok = false;
   string d1_bias = DailyBiasText(symbol_name, context_index, d1_ok);
   double atr14_m5_points = point > 0.0 ? AverageRangePrice(symbol_name, PERIOD_M5, 14, 1) / point : 0.0;
   datetime dubai_time = DubaiNow();

   string row[] = {
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      TimeToString(dubai_time, TIME_DATE | TIME_SECONDS),
      TimeBucketDubai(dubai_time),
      BoolText(state.observed_in_evening),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)),
      IntegerToString((long)state.ticket),
      IntegerToString(state.magic),
      state.candidate,
      state.comment,
      symbol_name,
      state.direction,
      DoubleToString(state.volume, 2),
      TimeToString(state.entry_time_broker, TIME_DATE | TIME_SECONDS),
      DoubleToString(state.entry_price, digits),
      DoubleToString(state.sl_last, digits),
      DoubleToString(state.tp_last, digits),
      DoubleToString(state.sl_initial, digits),
      DoubleToString(state.tp_initial, digits),
      DoubleToString(state.initial_stop_points, 2),
      DoubleToString(bid, digits),
      DoubleToString(ask, digits),
      DoubleToString(spread_points, 2),
      DoubleToString(exit_price, digits),
      DoubleToString(realized_pnl, 2),
      DoubleToString(realized_r, 4),
      DoubleToString(DistanceToSlPoints(state.direction, exit_price, state.sl_last, point), 2),
      DoubleToString(DistanceToTpPoints(state.direction, exit_price, state.tp_last, point), 2),
      DoubleToString(atr14_m5_points, 2),
      DoubleToString(m15_slope, 2),
      AvailabilityText(m15_ok),
      DoubleToString(h1_slope, 2),
      AvailabilityText(h1_ok),
      d1_bias,
      d1_ok ? "OK" : "D1_BIAS_UNAVAILABLE",
      IntegerToString(PositionsTotal()),
      "0",
      DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2),
      DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2),
      BoolText(BROKER_ACTION_ALLOWED),
      "CLOSE_DETECTED"
   };
   return AppendCsvRow(file_name, row);
}

bool WriteCloseSummary(PositionPathState &state)
{
   if(!EnsureSummaryHeader())
      return false;
   double exit_price = 0.0;
   datetime exit_time = 0;
   double realized_pnl = 0.0;
   string exit_reason = "NOT_FOUND";
   FindCloseDeal(state, exit_price, exit_time, realized_pnl, exit_reason);
   double point = SymbolInfoDouble(state.symbol_name, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(state.symbol_name, SYMBOL_DIGITS);
   double realized_r = 0.0;
   if(point > 0.0 && state.initial_stop_points > 0.0 && exit_price > 0.0)
   {
      double movement_points = state.direction == "BUY"
         ? (exit_price - state.entry_price) / point
         : (state.entry_price - exit_price) / point;
      realized_r = movement_points / state.initial_stop_points;
   }
   WriteCloseDetectedSnapshot(state, exit_price, realized_pnl, realized_r);
   datetime dubai_time = DubaiNow();
   string row[] = {
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      TimeToString(dubai_time, TIME_DATE | TIME_SECONDS),
      TimeBucketDubai(dubai_time),
      BoolText(state.observed_in_evening),
      InpRunId,
      IntegerToString((long)state.ticket),
      IntegerToString(state.magic),
      state.candidate,
      state.comment,
      state.symbol_name,
      state.direction,
      DoubleToString(state.volume, 2),
      TimeToString(state.entry_time_broker, TIME_DATE | TIME_SECONDS),
      exit_time > 0 ? TimeToString(exit_time, TIME_DATE | TIME_SECONDS) : "",
      DoubleToString(state.entry_price, digits),
      DoubleToString(exit_price, digits),
      DoubleToString(state.sl_initial, digits),
      DoubleToString(state.tp_initial, digits),
      DoubleToString(state.sl_last, digits),
      DoubleToString(state.tp_last, digits),
      exit_reason,
      DoubleToString(realized_pnl, 2),
      DoubleToString(realized_r, 4),
      SlippagePointsForExitText(state, exit_price, exit_reason),
      IntegerToString(state.snapshots_count),
      TimeToString(state.first_snapshot_utc, TIME_DATE | TIME_SECONDS),
      TimeToString(state.last_snapshot_utc, TIME_DATE | TIME_SECONDS),
      BoolText(BROKER_ACTION_ALLOWED)
   };
   return AppendCsvRow(InpSummaryFileName, row);
}

void DetectClosedPositions()
{
   for(int index = 0; index < MAX_TRACKED_POSITIONS; index++)
   {
      if(!g_positions[index].active)
         continue;
      if(TicketCurrentlyOpen(g_positions[index].ticket))
         continue;
      WriteCloseSummary(g_positions[index]);
      g_positions[index].active = false;
   }
}

void SnapshotOpenPositions()
{
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      string row_type = FindPositionStateIndex(ticket) >= 0 ? "SNAPSHOT" : "FIRST_SEEN";
      WriteSnapshotRow(ticket, row_type);
   }
   DetectClosedPositions();
}

int OnInit()
{
   if(!InpDryRunOnly)
   {
      Print("Phase2PositionPathObserver refused to start because dry-run mode is locked.");
      return INIT_FAILED;
   }
   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
   {
      Print("Phase2PositionPathObserver refused to start outside the expected demo server. Server=", server);
      return INIT_FAILED;
   }
   if(!EnsureStartupHeader() || !EnsureSummaryHeader() || !EnsureSnapshotHeader(SnapshotFileName()))
      return INIT_FAILED;

   int interval = InpSnapshotSeconds;
   if(interval < 1)
      interval = 10;
   WriteStartupRow("ATTACHED_POSITION_PATH_OBSERVER_TELEMETRY_ONLY");
   EventSetTimer(interval);
   SnapshotOpenPositions();
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   SnapshotOpenPositions();
   ReleaseSymbolContexts();
   string row[] = {
      TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
      TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS),
      TimeToString(DubaiNow(), TIME_DATE | TIME_SECONDS),
      InpRunId,
      AccountInfoString(ACCOUNT_SERVER),
      IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)),
      BoolText(InpDryRunOnly),
      BoolText(BROKER_ACTION_ALLOWED),
      IntegerToString(InpSnapshotSeconds),
      IntegerToString(InpDubaiUtcOffsetMinutes),
      "REMOVED_REASON_" + IntegerToString(reason)
   };
   AppendCsvRow(InpStartupFileName, row);
}

void OnTimer()
{
   SnapshotOpenPositions();
}
