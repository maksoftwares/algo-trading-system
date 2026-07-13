//+------------------------------------------------------------------+
//| A1XauRouterEntryHoldPathExporter.mq5                              |
//| Tester-only, zero-execution exporter for the frozen R1+R2 audit. |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - repository-only audit evidence"
#property version   "1.000"
#property strict
#property tester_file "a1_xau_router_entry_hold_path_schedule_v1.csv"

// This expert deliberately has no trading include and no execution surface.
// It follows outcome-free virtual positions supplied by an immutable schedule.

enum AuditTimeframeIndex
  {
   AUDIT_TF_D1 = 0,
   AUDIT_TF_H4 = 1,
   AUDIT_TF_H1 = 2,
   AUDIT_TF_M15 = 3,
   AUDIT_TF_M5 = 4,
   AUDIT_TF_COUNT = 5
  };

struct AuditEventKey
  {
   long tester_time_msc;
   long callback_sequence;
   long event_sequence;
  };

struct BarAvailability
  {
   bool          observed;
   datetime      current_bar_open;
   datetime      completed_bar_open;
   AuditEventKey observation_key;
  };

struct H1SlopeState
  {
   bool     valid;
   datetime completed_bar_open;
   double   close;
   double   ema20;
   double   ema50;
   double   ema20_slope_5_price;
   double   ema50_slope_5_price;
   double   ema20_slope_5_norm;
   double   abs_slope_q80;
   double   previous_close;
   double   previous_ema50;
   double   previous_ema20_slope_5_norm;
   double   previous_abs_slope_q80;
  };

struct TradeSessionInterval
  {
   int day_of_week;
   int from_seconds;
   int to_seconds;
  };

struct SnapshotCore
  {
   bool     valid;
   int      minimum_bar_shift;
   string   router_state;
   string   d1_structural_direction;
   string   h4_structural_direction;
   double   d1_close;
   double   d1_ema20;
   double   d1_ema50;
   double   d1_ema20_slope_5;
   double   d1_ema50_slope_5;
   double   h4_close;
   double   h4_ema20;
   double   h4_ema50;
   double   h4_ema20_slope_5;
   double   h4_ema50_slope_5;
   H1SlopeState h1;
   double   m15_close;
   double   m15_last_swing_high;
   datetime m15_last_swing_high_time;
   AuditEventKey m15_last_swing_high_confirmation_key;
   double   m15_last_swing_low;
   datetime m15_last_swing_low_time;
   AuditEventKey m15_last_swing_low_confirmation_key;
   string   m15_structure_break;
   BarAvailability availability[AUDIT_TF_COUNT];
  };

struct VirtualTrade
  {
   string trade_id;
   string source_id;
   string component;
   string expected_regime;
   string direction;
   datetime signal_time_broker;
   datetime entry_time_broker;
   datetime exit_time_broker;
   string native_run_id;
   string native_account;
   string native_symbol;
   string native_magic;
   string native_position_id;
   string native_entry_order;
   string native_entry_deal;
   string native_exit_order;
   string native_exit_deal;
   double executed_volume;
   double actual_entry_price;
   double original_sl;
   double original_tp;
   double order_bid;
   double order_ask;
   int    spread_points;
   double estimated_cost_r;
   string signal_reason;
   int    native_exit_reason_code;

   bool signal_emitted;
   bool entry_emitted;
   bool exit_emitted;
   bool active;
   bool failed;
   bool early_exit_trigger_seen;
   AuditEventKey signal_event_key;
   AuditEventKey entry_event_key;
   AuditEventKey exit_event_key;
   double initial_risk_usd;
   double independent_initial_risk_usd;
   double mfe_r;
   double mae_r;
   int holding_h1_bars;
  };

input string InpRunId = "A1_XAU_ROUTER_ENTRY_HOLD_PATH_EXPORT_20260710";
input string InpTargetSymbol = "XAUUSD";
input string InpScheduleFileName = "a1_xau_router_entry_hold_schedule.csv";
input string InpEventLogFileName = "a1_xau_router_entry_hold_events.csv";
input string InpFeatureLogFileName = "a1_xau_router_entry_hold_features.csv";
input string InpProvenanceLogFileName = "a1_xau_router_entry_hold_provenance.csv";
input string InpAssertionLogFileName = "a1_xau_router_entry_hold_assertions.csv";
input int    InpExpectedScheduleRows = 678;

// Frozen Router V1 contract. OnInit fails if any value is changed.
input int    InpAtrPeriod = 14;
input int    InpRegimeFastEmaPeriod = 20;
input int    InpRegimeSlowEmaPeriod = 50;
input int    InpRegimeSlopeLagBars = 5;
input int    InpRegimePersistenceD1Bars = 2;
input bool   InpRegimeRequireH4Confirm = true;
input double InpRegimeShockH1RangeAtrMultiple = 3.00;
input double InpRegimeShockD1AtrPercentileMin = 95.00;
input int    InpRegimeShockD1AtrLookback = 60;
input double InpRegimeCompressionD1AtrPercentileMax = 30.00;
input int    InpRegimeCompressionBoxDays = 5;
input double InpRegimeCompressionRangeMedianMax = 1.00;

const string AUDIT_SCHEMA_VERSION = "a1_xau_router_entry_hold_path_export_v1";
const string AUDIT_SOURCE_COMMIT = "006824cde421ea61a0bcdb074804f9ccf95c17a9";
const string AUDIT_ROUTER_SOURCE_SHA256 = "3372d8e751141f1d397d9967b8c14272046e1a733a64f67e63fcc3f56e53d355";
const int H1_Q80_WINDOW = 252;
const double H1_Q80_PROBABILITY = 0.80;

ENUM_TIMEFRAMES g_timeframes[AUDIT_TF_COUNT] =
  {
   PERIOD_D1,
   PERIOD_H4,
   PERIOD_H1,
   PERIOD_M15,
   PERIOD_M5
  };

string g_timeframe_names[AUDIT_TF_COUNT] = {"D1", "H4", "H1", "M15", "M5"};
BarAvailability g_bar_availability[AUDIT_TF_COUNT];
int g_ema20_handles[AUDIT_TF_COUNT];
int g_ema50_handles[AUDIT_TF_COUNT];
int g_atr_handles[AUDIT_TF_COUNT];

VirtualTrade g_trades[];
int g_active_trade_indices[];
TradeSessionInterval g_trade_sessions[];
int g_schedule_rows = 0;
int g_signal_events = 0;
int g_entry_events = 0;
int g_exit_events = 0;
int g_h1_hold_events = 0;
int g_next_signal_index = 0;
int g_next_entry_index = 0;

int g_event_handle = INVALID_HANDLE;
int g_feature_handle = INVALID_HANDLE;
int g_provenance_handle = INVALID_HANDLE;
int g_assertion_handle = INVALID_HANDLE;

long g_callback_sequence = 0;
long g_event_sequence = 0;
long g_current_tick_time_msc = 0;
long g_previous_tick_time_msc = 0;
MqlTick g_current_tick;
bool g_have_current_tick = false;
bool g_trade_session_open = false;
bool g_runtime_failed = false;
bool g_finalized = false;
bool g_timezone_written = false;
long g_last_broker_gmt_offset_seconds = 0;
string g_last_timezone_day = "";

H1SlopeState g_h1_slope_state;
SnapshotCore g_last_completed_h1_snapshot;
bool g_have_last_completed_h1_snapshot = false;

double g_last_confirmed_m15_swing_high = 0.0;
datetime g_last_confirmed_m15_swing_high_time = 0;
AuditEventKey g_last_confirmed_m15_swing_high_key;
double g_last_confirmed_m15_swing_low = 0.0;
datetime g_last_confirmed_m15_swing_low_time = 0;
AuditEventKey g_last_confirmed_m15_swing_low_key;

string BoolText(const bool value)
  {
   return value ? "true" : "false";
  }

AuditEventKey ZeroEventKey()
  {
   AuditEventKey key;
   key.tester_time_msc = 0;
   key.callback_sequence = 0;
   key.event_sequence = 0;
   return key;
  }

string EventKeyText(const AuditEventKey &key)
  {
   return IntegerToString(key.tester_time_msc) + "|" +
          IntegerToString(key.callback_sequence) + "|" +
          IntegerToString(key.event_sequence);
  }

string BrokerTimestamp(const datetime value)
  {
   if(value <= 0)
      return "";
   return TimeToString(value, TIME_DATE | TIME_SECONDS);
  }

string CurrentBrokerTimestamp()
  {
   if(!g_have_current_tick)
      return "";
   return BrokerTimestamp(g_current_tick.time);
  }

AuditEventKey NextEventKey()
  {
   g_event_sequence++;
   AuditEventKey key;
   key.tester_time_msc = g_current_tick_time_msc;
   key.callback_sequence = g_callback_sequence;
   key.event_sequence = g_event_sequence;
   return key;
  }

bool IsFinitePositive(const double value)
  {
   return MathIsValidNumber(value) && value > 0.0;
  }

bool NearlyEqual(const double left, const double right, const double tolerance = 0.0000001)
  {
   return MathAbs(left - right) <= tolerance;
  }

int SecondsOfDay(const datetime value)
  {
   MqlDateTime parts;
   if(!TimeToStruct(value, parts))
      return -1;
   return parts.hour * 3600 + parts.min * 60 + parts.sec;
  }

bool LoadTradeSessions()
  {
   ArrayResize(g_trade_sessions, 0);
   for(int day = 0; day < 7; day++)
     {
      for(uint session_index = 0; ; session_index++)
        {
         datetime session_from = 0;
         datetime session_to = 0;
         if(!SymbolInfoSessionTrade(
            InpTargetSymbol,
            (ENUM_DAY_OF_WEEK)day,
            session_index,
            session_from,
            session_to
         ))
            break;
         const int from_seconds = SecondsOfDay(session_from);
         const int to_seconds = SecondsOfDay(session_to);
         if(from_seconds < 0 || to_seconds < 0)
            return false;
         const int size = ArraySize(g_trade_sessions);
         ArrayResize(g_trade_sessions, size + 1);
         g_trade_sessions[size].day_of_week = day;
         g_trade_sessions[size].from_seconds = from_seconds;
         g_trade_sessions[size].to_seconds = to_seconds;
        }
     }
   return ArraySize(g_trade_sessions) > 0;
  }

bool TradeSessionOpenAt(const datetime value)
  {
   MqlDateTime parts;
   if(!TimeToStruct(value, parts))
      return false;
   const int seconds = parts.hour * 3600 + parts.min * 60 + parts.sec;
   for(int i = 0; i < ArraySize(g_trade_sessions); i++)
     {
      const TradeSessionInterval session = g_trade_sessions[i];
      if(session.day_of_week != parts.day_of_week)
         continue;
      if(session.from_seconds == session.to_seconds)
         return true;
      if(session.from_seconds < session.to_seconds &&
         seconds >= session.from_seconds && seconds < session.to_seconds)
         return true;
      if(session.from_seconds > session.to_seconds &&
         (seconds >= session.from_seconds || seconds < session.to_seconds))
         return true;
     }
   return false;
  }

void WriteAssertion(const string assertion_name, const string status, const string detail)
  {
   if(g_assertion_handle == INVALID_HANDLE)
      return;
   FileWrite(
      g_assertion_handle,
      AUDIT_SCHEMA_VERSION,
      InpRunId,
      IntegerToString(g_current_tick_time_msc),
      IntegerToString(g_callback_sequence),
      IntegerToString(g_event_sequence),
      CurrentBrokerTimestamp(),
      assertion_name,
      status,
      detail
   );
   if(status != "PASS")
      FileFlush(g_assertion_handle);
  }

void WriteProvenance(const string key, const string value, const string detail = "")
  {
   if(g_provenance_handle == INVALID_HANDLE)
      return;
   FileWrite(
      g_provenance_handle,
      AUDIT_SCHEMA_VERSION,
      InpRunId,
      IntegerToString(g_current_tick_time_msc),
      IntegerToString(g_callback_sequence),
      IntegerToString(g_event_sequence),
      CurrentBrokerTimestamp(),
      key,
      value,
      detail
   );
  }

AuditEventKey WriteEvent(
   const string stage,
   const int trade_index,
   const string timeframe,
   const datetime completed_bar_open,
   const bool position_open,
   const double executable_mark,
   const double unrealized_r,
   const double mfe_r_before_event,
   const double mae_r_before_event,
   const string status,
   const string detail
)
  {
   const AuditEventKey key = NextEventKey();
   string source_id = "";
   string component = "";
   string trade_id = "";
   string direction = "";
   string expected_regime = "";
   string native_position_id = "";
   int holding_h1_bars = 0;
   int native_exit_reason_code = 0;
   double initial_risk_usd = 0.0;
   double original_sl = 0.0;
   double original_tp = 0.0;
   int original_spread_points = 0;
   double estimated_cost_r = 0.0;
   if(trade_index >= 0 && trade_index < ArraySize(g_trades))
     {
      source_id = g_trades[trade_index].source_id;
      component = g_trades[trade_index].component;
      trade_id = g_trades[trade_index].trade_id;
      direction = g_trades[trade_index].direction;
      expected_regime = g_trades[trade_index].expected_regime;
      native_position_id = g_trades[trade_index].native_position_id;
      holding_h1_bars = g_trades[trade_index].holding_h1_bars;
      native_exit_reason_code = g_trades[trade_index].native_exit_reason_code;
      initial_risk_usd = g_trades[trade_index].initial_risk_usd;
      original_sl = g_trades[trade_index].original_sl;
      original_tp = g_trades[trade_index].original_tp;
      original_spread_points = g_trades[trade_index].spread_points;
      estimated_cost_r = g_trades[trade_index].estimated_cost_r;
     }

   FileWrite(
      g_event_handle,
      AUDIT_SCHEMA_VERSION,
      InpRunId,
      stage,
      IntegerToString(key.tester_time_msc),
      IntegerToString(key.callback_sequence),
      IntegerToString(key.event_sequence),
      CurrentBrokerTimestamp(),
      BrokerTimestamp(TimeGMT()),
      BrokerTimestamp(TimeTradeServer()),
      source_id,
      component,
      trade_id,
      direction,
      expected_regime,
      native_position_id,
      timeframe,
      BrokerTimestamp(completed_bar_open),
      BoolText(position_open),
      DoubleToString(g_current_tick.bid, _Digits),
      DoubleToString(g_current_tick.ask, _Digits),
      IntegerToString((long)g_current_tick.flags),
      BoolText(g_trade_session_open),
      DoubleToString(executable_mark, _Digits),
      DoubleToString(initial_risk_usd, 10),
      DoubleToString(unrealized_r, 10),
      DoubleToString(mfe_r_before_event, 10),
      DoubleToString(mae_r_before_event, 10),
      IntegerToString(holding_h1_bars),
      IntegerToString(native_exit_reason_code),
      DoubleToString(original_sl, _Digits),
      DoubleToString(original_tp, _Digits),
      IntegerToString(original_spread_points),
      DoubleToString(estimated_cost_r, 10),
      status,
      detail
   );
   return key;
  }

void RuntimeFailure(const string assertion_name, const string detail, const int trade_index = -1)
  {
   g_runtime_failed = true;
   WriteAssertion(assertion_name, "FAIL", detail);
   if(g_have_current_tick && g_event_handle != INVALID_HANDLE)
      WriteEvent("RUNTIME_ERROR", trade_index, "", 0, false, 0.0, 0.0, 0.0, 0.0, "FAIL", assertion_name + ":" + detail);
  }

bool OpenOutputLogs()
  {
   g_event_handle = FileOpen(InpEventLogFileName, FILE_WRITE | FILE_CSV | FILE_ANSI, '\t');
   g_feature_handle = FileOpen(InpFeatureLogFileName, FILE_WRITE | FILE_CSV | FILE_ANSI, '\t');
   g_provenance_handle = FileOpen(InpProvenanceLogFileName, FILE_WRITE | FILE_CSV | FILE_ANSI, '\t');
   g_assertion_handle = FileOpen(InpAssertionLogFileName, FILE_WRITE | FILE_CSV | FILE_ANSI, '\t');
   if(g_event_handle == INVALID_HANDLE || g_feature_handle == INVALID_HANDLE ||
      g_provenance_handle == INVALID_HANDLE || g_assertion_handle == INVALID_HANDLE)
      return false;

   FileWrite(
      g_event_handle,
      "schema_version", "run_id", "stage", "tester_time_msc", "callback_sequence", "event_sequence",
      "timestamp_broker", "timestamp_gmt", "timestamp_trade_server", "source_id", "component", "trade_id",
      "direction", "expected_regime", "native_position_id", "timeframe", "completed_bar_open", "position_open",
      "bid", "ask", "tick_flags", "trade_session_open", "executable_mark", "initial_risk_usd", "unrealized_r", "mfe_r_before_event",
      "mae_r_before_event", "holding_h1_bars", "native_exit_reason_code", "original_sl", "original_tp",
      "original_spread_points", "estimated_cost_r", "status", "detail"
   );
   FileWrite(
      g_feature_handle,
      "schema_version", "run_id", "stage", "tester_time_msc", "callback_sequence", "event_sequence",
      "timestamp_broker", "source_id", "component", "trade_id", "direction", "expected_regime",
      "minimum_bar_shift", "router_state", "d1_bar_available_key", "d1_close", "d1_ema20", "d1_ema50",
      "d1_ema20_slope_5", "d1_ema50_slope_5", "d1_structural_direction", "h4_bar_available_key",
      "h4_close", "h4_ema20", "h4_ema50", "h4_ema20_slope_5", "h4_ema50_slope_5",
      "h4_structural_direction", "h4_expected_stack", "h1_bar_available_key", "h1_close", "h1_ema20",
      "h1_ema50", "h1_ema20_slope_5_price", "h1_ema50_slope_5_price", "h1_ema20_slope_5_norm",
      "h1_abs_slope_q80", "h1_previous_close", "h1_previous_ema50", "h1_previous_ema20_slope_5_norm",
      "h1_previous_abs_slope_q80", "m15_bar_available_key", "m15_close", "m15_last_confirmed_swing_high",
      "m15_swing_high_time", "m15_swing_high_confirmation_key", "m15_last_confirmed_swing_low",
      "m15_swing_low_time", "m15_swing_low_confirmation_key", "m15_structure_break", "m5_bar_available_key",
      "m5_signal_state", "bid", "ask", "current_spread_points", "initial_risk_usd", "original_sl", "original_tp"
   );
   FileWrite(
      g_provenance_handle,
      "schema_version", "run_id", "tester_time_msc", "callback_sequence", "event_sequence",
      "timestamp_broker", "key", "value", "detail"
   );
   FileWrite(
      g_assertion_handle,
      "schema_version", "run_id", "tester_time_msc", "callback_sequence", "event_sequence",
      "timestamp_broker", "assertion", "status", "detail"
   );
   return true;
  }

void CloseOutputLogs()
  {
   if(g_event_handle != INVALID_HANDLE)
     {
      FileFlush(g_event_handle);
      FileClose(g_event_handle);
      g_event_handle = INVALID_HANDLE;
     }
   if(g_feature_handle != INVALID_HANDLE)
     {
      FileFlush(g_feature_handle);
      FileClose(g_feature_handle);
      g_feature_handle = INVALID_HANDLE;
     }
   if(g_provenance_handle != INVALID_HANDLE)
     {
      FileFlush(g_provenance_handle);
      FileClose(g_provenance_handle);
      g_provenance_handle = INVALID_HANDLE;
     }
   if(g_assertion_handle != INVALID_HANDLE)
     {
      FileFlush(g_assertion_handle);
      FileClose(g_assertion_handle);
      g_assertion_handle = INVALID_HANDLE;
     }
  }

bool FrozenInputsMatch()
  {
   return InpAtrPeriod == 14 &&
          InpRegimeFastEmaPeriod == 20 &&
          InpRegimeSlowEmaPeriod == 50 &&
          InpRegimeSlopeLagBars == 5 &&
          InpRegimePersistenceD1Bars == 2 &&
          InpRegimeRequireH4Confirm &&
          NearlyEqual(InpRegimeShockH1RangeAtrMultiple, 3.00) &&
          NearlyEqual(InpRegimeShockD1AtrPercentileMin, 95.00) &&
          InpRegimeShockD1AtrLookback == 60 &&
          NearlyEqual(InpRegimeCompressionD1AtrPercentileMax, 30.00) &&
          InpRegimeCompressionBoxDays == 5 &&
          NearlyEqual(InpRegimeCompressionRangeMedianMax, 1.00);
  }

string ExpectedSignalReason(const string source_id)
  {
   if(source_id == "h4_d1_long_best_box2_atr80")
      return "D1_COMPRESSION_H4_EXPANSION_LONG";
   if(source_id == "r1_h1_pullback_long_v1")
      return "R1_H1_EMA_PULLBACK_LONG_M15";
   if(source_id == "r2_continuation_short_v1")
      return "BEAR_DOWNSIDE_IMPULSE_RETEST_SHORT";
   if(source_id == "r2_pullback_rejection_short_v1")
      return "R2_H1_EMA_PULLBACK_REJECTION_SHORT_H1";
   return "";
  }

bool SourceContractMatches(const VirtualTrade &trade)
  {
   if(trade.source_id == "h4_d1_long_best_box2_atr80" || trade.source_id == "r1_h1_pullback_long_v1")
      return trade.component == "R1" && trade.direction == "LONG" && trade.expected_regime == "UPTREND";
   if(trade.source_id == "r2_continuation_short_v1" || trade.source_id == "r2_pullback_rejection_short_v1")
      return trade.component == "R2" && trade.direction == "SHORT" && trade.expected_regime == "DOWNTREND";
   return false;
  }

bool HasValidNamespacedTradeId(const string value)
  {
   if(value == "" || StringFind(value, "::") <= 0)
      return false;
   int separators = 0;
   int cursor = 0;
   while(true)
     {
      const int position = StringFind(value, "::", cursor);
      if(position < 0)
         break;
      if(position == cursor)
         return false;
      separators++;
      cursor = position + 2;
     }
   return separators == 5 && cursor < StringLen(value);
  }

bool HeaderFieldMatches(const int handle, const string expected)
  {
   if(FileIsEnding(handle))
      return false;
   return FileReadString(handle) == expected;
  }

bool ReadAndValidateScheduleHeader(const int handle)
  {
   string expected[] =
     {
      "trade_id", "source_id", "component", "expected_regime", "direction", "signal_time_broker",
      "entry_time_broker", "exit_time_broker", "native_run_id", "native_account", "native_symbol",
      "native_magic", "native_position_id", "native_entry_order", "native_entry_deal", "native_exit_order",
      "native_exit_deal", "executed_volume", "actual_entry_price", "original_sl", "original_tp", "order_bid",
      "order_ask", "spread_points", "estimated_cost_r", "signal_reason", "native_exit_reason_code"
     };
   for(int i = 0; i < ArraySize(expected); i++)
     {
      if(!HeaderFieldMatches(handle, expected[i]))
         return false;
     }
   return true;
  }

bool LoadSchedule()
  {
   const int handle = FileOpen(InpScheduleFileName, FILE_READ | FILE_CSV | FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
     {
      WriteAssertion("schedule_file_open", "FAIL", InpScheduleFileName);
      return false;
     }
   if(!ReadAndValidateScheduleHeader(handle))
     {
      FileClose(handle);
      WriteAssertion("schedule_header_exact", "FAIL", "unexpected schedule schema");
      return false;
     }

   int source_h4 = 0;
   int source_r1 = 0;
   int source_r2_continuation = 0;
   int source_r2_pullback = 0;
   datetime previous_signal_time = 0;
   datetime previous_entry_time = 0;
   while(!FileIsEnding(handle))
     {
      VirtualTrade trade;
      trade.trade_id = FileReadString(handle);
      if(trade.trade_id == "" && FileIsEnding(handle))
         break;
      trade.source_id = FileReadString(handle);
      trade.component = FileReadString(handle);
      trade.expected_regime = FileReadString(handle);
      trade.direction = FileReadString(handle);
      trade.signal_time_broker = StringToTime(FileReadString(handle));
      trade.entry_time_broker = StringToTime(FileReadString(handle));
      trade.exit_time_broker = StringToTime(FileReadString(handle));
      trade.native_run_id = FileReadString(handle);
      trade.native_account = FileReadString(handle);
      trade.native_symbol = FileReadString(handle);
      trade.native_magic = FileReadString(handle);
      trade.native_position_id = FileReadString(handle);
      trade.native_entry_order = FileReadString(handle);
      trade.native_entry_deal = FileReadString(handle);
      trade.native_exit_order = FileReadString(handle);
      trade.native_exit_deal = FileReadString(handle);
      trade.executed_volume = StringToDouble(FileReadString(handle));
      trade.actual_entry_price = StringToDouble(FileReadString(handle));
      trade.original_sl = StringToDouble(FileReadString(handle));
      trade.original_tp = StringToDouble(FileReadString(handle));
      trade.order_bid = StringToDouble(FileReadString(handle));
      trade.order_ask = StringToDouble(FileReadString(handle));
      trade.spread_points = (int)StringToInteger(FileReadString(handle));
      trade.estimated_cost_r = StringToDouble(FileReadString(handle));
      trade.signal_reason = FileReadString(handle);
      trade.native_exit_reason_code = (int)StringToInteger(FileReadString(handle));

      trade.signal_emitted = false;
      trade.entry_emitted = false;
      trade.exit_emitted = false;
      trade.active = false;
      trade.failed = false;
      trade.early_exit_trigger_seen = false;
      trade.signal_event_key = ZeroEventKey();
      trade.entry_event_key = ZeroEventKey();
      trade.exit_event_key = ZeroEventKey();
      trade.initial_risk_usd = 0.0;
      trade.independent_initial_risk_usd = 0.0;
      trade.mfe_r = 0.0;
      trade.mae_r = 0.0;
      trade.holding_h1_bars = 0;

      const int row_number = ArraySize(g_trades) + 2;
      bool valid = true;
      valid = valid && HasValidNamespacedTradeId(trade.trade_id);
      valid = valid && SourceContractMatches(trade);
      valid = valid && trade.signal_reason == ExpectedSignalReason(trade.source_id);
      valid = valid && trade.signal_time_broker > 0 && trade.entry_time_broker > 0 && trade.exit_time_broker > 0;
      valid = valid && trade.signal_time_broker <= trade.entry_time_broker && trade.entry_time_broker < trade.exit_time_broker;
      valid = valid && previous_signal_time < trade.signal_time_broker;
      valid = valid && previous_entry_time < trade.entry_time_broker;
      valid = valid && trade.native_run_id != "" && trade.native_account != "" && trade.native_symbol == InpTargetSymbol;
      valid = valid && trade.native_magic != "" && trade.native_position_id != "";
      valid = valid && trade.native_entry_order != "" && trade.native_entry_deal != "";
      valid = valid && trade.native_exit_order != "" && trade.native_exit_deal != "";
      valid = valid && IsFinitePositive(trade.executed_volume) && IsFinitePositive(trade.actual_entry_price);
      valid = valid && IsFinitePositive(trade.original_sl) && IsFinitePositive(trade.original_tp);
      valid = valid && IsFinitePositive(trade.order_bid) && IsFinitePositive(trade.order_ask) && trade.order_ask >= trade.order_bid;
      valid = valid && trade.spread_points >= 0 && MathIsValidNumber(trade.estimated_cost_r) && trade.estimated_cost_r >= 0.0;
      valid = valid && (trade.native_exit_reason_code == (int)DEAL_REASON_SL || trade.native_exit_reason_code == (int)DEAL_REASON_TP);
      if(!valid)
        {
         FileClose(handle);
         WriteAssertion("schedule_row_valid", "FAIL", "row=" + IntegerToString(row_number));
         return false;
        }
      previous_signal_time = trade.signal_time_broker;
      previous_entry_time = trade.entry_time_broker;

      const int index = ArraySize(g_trades);
      ArrayResize(g_trades, index + 1);
      g_trades[index] = trade;
      if(trade.source_id == "h4_d1_long_best_box2_atr80")
         source_h4++;
      else if(trade.source_id == "r1_h1_pullback_long_v1")
         source_r1++;
      else if(trade.source_id == "r2_continuation_short_v1")
         source_r2_continuation++;
      else if(trade.source_id == "r2_pullback_rejection_short_v1")
         source_r2_pullback++;
     }
   FileClose(handle);

   g_schedule_rows = ArraySize(g_trades);
   if(g_schedule_rows != InpExpectedScheduleRows || source_h4 != 145 || source_r1 != 413 ||
      source_r2_continuation != 57 || source_r2_pullback != 63)
     {
      WriteAssertion(
         "schedule_source_counts",
         "FAIL",
         "total=" + IntegerToString(g_schedule_rows) +
         ",h4=" + IntegerToString(source_h4) +
         ",r1=" + IntegerToString(source_r1) +
         ",r2c=" + IntegerToString(source_r2_continuation) +
         ",r2p=" + IntegerToString(source_r2_pullback)
      );
      return false;
     }
   WriteAssertion("schedule_header_exact", "PASS", "27 outcome-free fields");
   WriteAssertion("schedule_source_counts", "PASS", "145/413/57/63 total=678");
   return true;
  }

bool InitializeIndicatorHandles()
  {
   for(int i = 0; i < AUDIT_TF_COUNT; i++)
     {
      g_ema20_handles[i] = iMA(InpTargetSymbol, g_timeframes[i], InpRegimeFastEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
      g_ema50_handles[i] = iMA(InpTargetSymbol, g_timeframes[i], InpRegimeSlowEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
      g_atr_handles[i] = iATR(InpTargetSymbol, g_timeframes[i], InpAtrPeriod);
      if(g_ema20_handles[i] == INVALID_HANDLE || g_ema50_handles[i] == INVALID_HANDLE || g_atr_handles[i] == INVALID_HANDLE)
         return false;
     }
   return true;
  }

void ReleaseIndicatorHandles()
  {
   for(int i = 0; i < AUDIT_TF_COUNT; i++)
     {
      if(g_ema20_handles[i] != INVALID_HANDLE)
         IndicatorRelease(g_ema20_handles[i]);
      if(g_ema50_handles[i] != INVALID_HANDLE)
         IndicatorRelease(g_ema50_handles[i]);
      if(g_atr_handles[i] != INVALID_HANDLE)
         IndicatorRelease(g_atr_handles[i]);
      g_ema20_handles[i] = INVALID_HANDLE;
      g_ema50_handles[i] = INVALID_HANDLE;
      g_atr_handles[i] = INVALID_HANDLE;
     }
  }

double IndicatorValue(const int handle, const int shift)
  {
   if(handle == INVALID_HANDLE || shift < 1)
      return 0.0;
   double values[1];
   if(CopyBuffer(handle, 0, shift, 1, values) != 1)
      return 0.0;
   return values[0];
  }

double Ema20Value(const int timeframe_index, const int shift)
  {
   return IndicatorValue(g_ema20_handles[timeframe_index], shift);
  }

double Ema50Value(const int timeframe_index, const int shift)
  {
   return IndicatorValue(g_ema50_handles[timeframe_index], shift);
  }

double AtrValue(const int timeframe_index, const int shift)
  {
   return IndicatorValue(g_atr_handles[timeframe_index], shift);
  }

double Type7Quantile80(double &values[])
  {
   if(ArraySize(values) != H1_Q80_WINDOW)
      return 0.0;
   ArraySort(values);
   const double h = (double)(H1_Q80_WINDOW - 1) * H1_Q80_PROBABILITY;
   const int lower = (int)MathFloor(h);
   const int upper = (int)MathCeil(h);
   const double weight = h - (double)lower;
   return values[lower] + (values[upper] - values[lower]) * weight;
  }

bool ComputeH1SlopeState(H1SlopeState &state)
  {
   state.valid = false;
   const int required_values = 259;
   double ema20_values[];
   double ema50_values[];
   double atr_values[];
   ArrayResize(ema20_values, required_values);
   ArrayResize(ema50_values, required_values);
   ArrayResize(atr_values, required_values);
   ArraySetAsSeries(ema20_values, true);
   ArraySetAsSeries(ema50_values, true);
   ArraySetAsSeries(atr_values, true);
   if(CopyBuffer(g_ema20_handles[AUDIT_TF_H1], 0, 1, required_values, ema20_values) != required_values ||
      CopyBuffer(g_ema50_handles[AUDIT_TF_H1], 0, 1, required_values, ema50_values) != required_values ||
      CopyBuffer(g_atr_handles[AUDIT_TF_H1], 0, 1, required_values, atr_values) != required_values)
      return false;

   const int current_shift = 1;
   const int previous_shift = 2;
   const int current_window_first_shift = 2;
   const int previous_window_first_shift = 3;
   double current_window[];
   double previous_window[];
   ArrayResize(current_window, H1_Q80_WINDOW);
   ArrayResize(previous_window, H1_Q80_WINDOW);
   for(int i = 0; i < H1_Q80_WINDOW; i++)
     {
      const int current_window_shift = current_window_first_shift + i;
      const int previous_window_shift = previous_window_first_shift + i;
      const int current_index = current_window_shift - 1;
      const int previous_index = previous_window_shift - 1;
      const double current_atr = atr_values[current_index];
      const double previous_atr = atr_values[previous_index];
      if(!IsFinitePositive(current_atr) || !IsFinitePositive(previous_atr))
         return false;
      const double current_norm =
         (ema20_values[current_index] - ema20_values[current_index + InpRegimeSlopeLagBars]) / current_atr;
      const double previous_norm =
         (ema20_values[previous_index] - ema20_values[previous_index + InpRegimeSlopeLagBars]) / previous_atr;
      if(!MathIsValidNumber(current_norm) || !MathIsValidNumber(previous_norm))
         return false;
      current_window[i] = MathAbs(current_norm);
      previous_window[i] = MathAbs(previous_norm);
     }

   const int current_index = current_shift - 1;
   const int previous_index = previous_shift - 1;
   if(!IsFinitePositive(atr_values[current_index]) || !IsFinitePositive(atr_values[previous_index]))
      return false;
   state.completed_bar_open = iTime(InpTargetSymbol, PERIOD_H1, 1);
   state.close = iClose(InpTargetSymbol, PERIOD_H1, 1);
   state.ema20 = ema20_values[current_index];
   state.ema50 = ema50_values[current_index];
   state.ema20_slope_5_price = ema20_values[current_index] - ema20_values[current_index + InpRegimeSlopeLagBars];
   state.ema50_slope_5_price = ema50_values[current_index] - ema50_values[current_index + InpRegimeSlopeLagBars];
   state.ema20_slope_5_norm = state.ema20_slope_5_price / atr_values[current_index];
   state.abs_slope_q80 = Type7Quantile80(current_window);
   state.previous_close = iClose(InpTargetSymbol, PERIOD_H1, 2);
   state.previous_ema50 = ema50_values[previous_index];
   state.previous_ema20_slope_5_norm =
      (ema20_values[previous_index] - ema20_values[previous_index + InpRegimeSlopeLagBars]) / atr_values[previous_index];
   state.previous_abs_slope_q80 = Type7Quantile80(previous_window);
   state.valid = IsFinitePositive(state.close) && IsFinitePositive(state.ema20) && IsFinitePositive(state.ema50) &&
                 MathIsValidNumber(state.ema20_slope_5_norm) && IsFinitePositive(state.abs_slope_q80) &&
                 IsFinitePositive(state.previous_close) && IsFinitePositive(state.previous_ema50) &&
                 MathIsValidNumber(state.previous_ema20_slope_5_norm) && IsFinitePositive(state.previous_abs_slope_q80);
   return state.valid;
  }

bool TrendStackAtShift(const int timeframe_index, const int shift, const bool uptrend)
  {
   if(shift < 1)
      return false;
   const ENUM_TIMEFRAMES timeframe = g_timeframes[timeframe_index];
   const double close = iClose(InpTargetSymbol, timeframe, shift);
   const double fast_now = Ema20Value(timeframe_index, shift);
   const double slow_now = Ema50Value(timeframe_index, shift);
   const double fast_prior = Ema20Value(timeframe_index, shift + InpRegimeSlopeLagBars);
   const double slow_prior = Ema50Value(timeframe_index, shift + InpRegimeSlopeLagBars);
   if(!IsFinitePositive(close) || !IsFinitePositive(fast_now) || !IsFinitePositive(slow_now) ||
      !IsFinitePositive(fast_prior) || !IsFinitePositive(slow_prior))
      return false;
   if(uptrend)
      return close > fast_now && fast_now > slow_now && fast_now >= fast_prior && slow_now >= slow_prior;
   return close < fast_now && fast_now < slow_now && fast_now <= fast_prior && slow_now <= slow_prior;
  }

string StructuralDirection(const int timeframe_index)
  {
   if(TrendStackAtShift(timeframe_index, 1, true))
      return "UP";
   if(TrendStackAtShift(timeframe_index, 1, false))
      return "DOWN";
   return "NONE";
  }

double AtrPercentile(const int timeframe_index, const int lookback, const int shift)
  {
   if(shift < 1 || lookback <= 0)
      return 100.0;
   const double current_atr = AtrValue(timeframe_index, shift);
   if(!IsFinitePositive(current_atr))
      return 100.0;
   int valid = 0;
   int less_or_equal = 0;
   for(int i = 0; i < lookback; i++)
     {
      const double value = AtrValue(timeframe_index, shift + i);
      if(!IsFinitePositive(value))
         continue;
      valid++;
      if(value <= current_atr)
         less_or_equal++;
     }
   if(valid <= 0)
      return 100.0;
   return 100.0 * (double)less_or_equal / (double)valid;
  }

double TimeframeHigh(const ENUM_TIMEFRAMES timeframe, const int start_shift, const int count)
  {
   if(start_shift < 1 || count <= 0)
      return 0.0;
   double value = 0.0;
   for(int i = 0; i < count; i++)
     {
      const double item = iHigh(InpTargetSymbol, timeframe, start_shift + i);
      if(!IsFinitePositive(item))
         return 0.0;
      if(value == 0.0 || item > value)
         value = item;
     }
   return value;
  }

double TimeframeLow(const ENUM_TIMEFRAMES timeframe, const int start_shift, const int count)
  {
   if(start_shift < 1 || count <= 0)
      return 0.0;
   double value = 0.0;
   for(int i = 0; i < count; i++)
     {
      const double item = iLow(InpTargetSymbol, timeframe, start_shift + i);
      if(!IsFinitePositive(item))
         return 0.0;
      if(value == 0.0 || item < value)
         value = item;
     }
   return value;
  }

double TimeframeMedianRange(const ENUM_TIMEFRAMES timeframe, const int count, const int start_shift)
  {
   if(start_shift < 1 || count <= 0)
      return 0.0;
   double ranges[];
   ArrayResize(ranges, count);
   for(int i = 0; i < count; i++)
     {
      const double high = iHigh(InpTargetSymbol, timeframe, start_shift + i);
      const double low = iLow(InpTargetSymbol, timeframe, start_shift + i);
      if(!IsFinitePositive(high) || !IsFinitePositive(low) || high <= low)
         return 0.0;
      ranges[i] = high - low;
     }
   ArraySort(ranges);
   if((count % 2) == 1)
      return ranges[count / 2];
   return 0.5 * (ranges[count / 2 - 1] + ranges[count / 2]);
  }

bool D1TrendPersists(const bool uptrend)
  {
   for(int shift = 1; shift <= InpRegimePersistenceD1Bars; shift++)
     {
      if(!TrendStackAtShift(AUDIT_TF_D1, shift, uptrend))
         return false;
     }
   return true;
  }

bool H4TrendConfirms(const bool uptrend)
  {
   if(!InpRegimeRequireH4Confirm)
      return true;
   return TrendStackAtShift(AUDIT_TF_H4, 1, uptrend);
  }

bool ShockState()
  {
   const double h1_high = iHigh(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_low = iLow(InpTargetSymbol, PERIOD_H1, 1);
   const double h1_atr = AtrValue(AUDIT_TF_H1, 1);
   if(IsFinitePositive(h1_high) && IsFinitePositive(h1_low) && h1_high > h1_low && IsFinitePositive(h1_atr) &&
      (h1_high - h1_low) >= InpRegimeShockH1RangeAtrMultiple * h1_atr)
      return true;
   return AtrPercentile(AUDIT_TF_D1, InpRegimeShockD1AtrLookback, 1) >= InpRegimeShockD1AtrPercentileMin;
  }

bool CompressionState()
  {
   const double d1_atr_percentile = AtrPercentile(AUDIT_TF_D1, 252, 1);
   const double box_high = TimeframeHigh(PERIOD_D1, 1, InpRegimeCompressionBoxDays);
   const double box_low = TimeframeLow(PERIOD_D1, 1, InpRegimeCompressionBoxDays);
   const double median_range = TimeframeMedianRange(PERIOD_D1, 20, 1);
   const double box_width = box_high - box_low;
   if(!IsFinitePositive(box_high) || !IsFinitePositive(box_low) || !IsFinitePositive(box_width) || !IsFinitePositive(median_range))
      return false;
   const double box_average = box_width / (double)InpRegimeCompressionBoxDays;
   return d1_atr_percentile <= InpRegimeCompressionD1AtrPercentileMax &&
          box_average <= InpRegimeCompressionRangeMedianMax * median_range;
  }

string CurrentRouterState()
  {
   if(ShockState())
      return "SHOCK";
   if(D1TrendPersists(true) && H4TrendConfirms(true))
      return "UPTREND";
   if(D1TrendPersists(false) && H4TrendConfirms(false))
      return "DOWNTREND";
   if(CompressionState())
      return "COMPRESSION";
   return "CHOP";
  }

void UpdateM15Pivots(const AuditEventKey &confirmation_key)
  {
   // At the first tick of a new M15 bar, shift 1 is k+2 and shift 3 is k.
   const int candidate_shift = 3;
   const double candidate_high = iHigh(InpTargetSymbol, PERIOD_M15, candidate_shift);
   const double candidate_low = iLow(InpTargetSymbol, PERIOD_M15, candidate_shift);
   const bool high_confirmed =
      candidate_high > iHigh(InpTargetSymbol, PERIOD_M15, 5) &&
      candidate_high > iHigh(InpTargetSymbol, PERIOD_M15, 4) &&
      candidate_high > iHigh(InpTargetSymbol, PERIOD_M15, 2) &&
      candidate_high > iHigh(InpTargetSymbol, PERIOD_M15, 1);
   const bool low_confirmed =
      candidate_low < iLow(InpTargetSymbol, PERIOD_M15, 5) &&
      candidate_low < iLow(InpTargetSymbol, PERIOD_M15, 4) &&
      candidate_low < iLow(InpTargetSymbol, PERIOD_M15, 2) &&
      candidate_low < iLow(InpTargetSymbol, PERIOD_M15, 1);
   if(IsFinitePositive(candidate_high) && high_confirmed)
     {
      g_last_confirmed_m15_swing_high = candidate_high;
      g_last_confirmed_m15_swing_high_time = iTime(InpTargetSymbol, PERIOD_M15, candidate_shift);
      g_last_confirmed_m15_swing_high_key = confirmation_key;
     }
   if(IsFinitePositive(candidate_low) && low_confirmed)
     {
      g_last_confirmed_m15_swing_low = candidate_low;
      g_last_confirmed_m15_swing_low_time = iTime(InpTargetSymbol, PERIOD_M15, candidate_shift);
      g_last_confirmed_m15_swing_low_key = confirmation_key;
     }
  }

string CurrentM15StructureBreak(const double close)
  {
   if(!IsFinitePositive(close) || !IsFinitePositive(g_last_confirmed_m15_swing_high) ||
      !IsFinitePositive(g_last_confirmed_m15_swing_low))
      return "UNKNOWN";
   const bool above_high = close > g_last_confirmed_m15_swing_high;
   const bool below_low = close < g_last_confirmed_m15_swing_low;
   if(above_high && !below_low)
      return "BULLISH";
   if(!above_high && below_low)
      return "BEARISH";
   if(!above_high && !below_low)
      return "NONE";
   return "AMBIGUOUS";
  }

bool ObserveCompletedBar(const int timeframe_index)
  {
   const ENUM_TIMEFRAMES timeframe = g_timeframes[timeframe_index];
   const datetime current_open = iTime(InpTargetSymbol, timeframe, 0);
   if(current_open <= 0)
     {
      RuntimeFailure("bar_current_open_available", g_timeframe_names[timeframe_index]);
      return false;
     }
   if(g_bar_availability[timeframe_index].observed &&
      current_open == g_bar_availability[timeframe_index].current_bar_open)
      return false;
   if(g_bar_availability[timeframe_index].observed &&
      current_open < g_bar_availability[timeframe_index].current_bar_open)
     {
      RuntimeFailure("bar_time_monotone", g_timeframe_names[timeframe_index]);
      return false;
     }
   const datetime completed_open = iTime(InpTargetSymbol, timeframe, 1);
   if(completed_open <= 0 || completed_open >= current_open)
     {
      RuntimeFailure("completed_bar_shift_one", g_timeframe_names[timeframe_index]);
      return false;
     }
   const AuditEventKey key = WriteEvent(
      "BAR_AVAILABLE", -1, g_timeframe_names[timeframe_index], completed_open, false,
      0.0, 0.0, 0.0, 0.0, "PASS", "minimum_bar_shift=1"
   );
   g_bar_availability[timeframe_index].observed = true;
   g_bar_availability[timeframe_index].current_bar_open = current_open;
   g_bar_availability[timeframe_index].completed_bar_open = completed_open;
   g_bar_availability[timeframe_index].observation_key = key;
   if(timeframe_index == AUDIT_TF_M15)
      UpdateM15Pivots(key);
   return true;
  }

bool BuildSnapshotCore(SnapshotCore &snapshot)
  {
   snapshot.valid = false;
   snapshot.minimum_bar_shift = 1;
   for(int i = 0; i < AUDIT_TF_COUNT; i++)
     {
      if(!g_bar_availability[i].observed)
         return false;
      snapshot.availability[i] = g_bar_availability[i];
     }
   snapshot.router_state = CurrentRouterState();
   snapshot.d1_structural_direction = StructuralDirection(AUDIT_TF_D1);
   snapshot.h4_structural_direction = StructuralDirection(AUDIT_TF_H4);
   snapshot.d1_close = iClose(InpTargetSymbol, PERIOD_D1, 1);
   snapshot.d1_ema20 = Ema20Value(AUDIT_TF_D1, 1);
   snapshot.d1_ema50 = Ema50Value(AUDIT_TF_D1, 1);
   snapshot.d1_ema20_slope_5 = snapshot.d1_ema20 - Ema20Value(AUDIT_TF_D1, 1 + InpRegimeSlopeLagBars);
   snapshot.d1_ema50_slope_5 = snapshot.d1_ema50 - Ema50Value(AUDIT_TF_D1, 1 + InpRegimeSlopeLagBars);
   snapshot.h4_close = iClose(InpTargetSymbol, PERIOD_H4, 1);
   snapshot.h4_ema20 = Ema20Value(AUDIT_TF_H4, 1);
   snapshot.h4_ema50 = Ema50Value(AUDIT_TF_H4, 1);
   snapshot.h4_ema20_slope_5 = snapshot.h4_ema20 - Ema20Value(AUDIT_TF_H4, 1 + InpRegimeSlopeLagBars);
   snapshot.h4_ema50_slope_5 = snapshot.h4_ema50 - Ema50Value(AUDIT_TF_H4, 1 + InpRegimeSlopeLagBars);
   snapshot.h1 = g_h1_slope_state;
   snapshot.m15_close = iClose(InpTargetSymbol, PERIOD_M15, 1);
   snapshot.m15_last_swing_high = g_last_confirmed_m15_swing_high;
   snapshot.m15_last_swing_high_time = g_last_confirmed_m15_swing_high_time;
   snapshot.m15_last_swing_high_confirmation_key = g_last_confirmed_m15_swing_high_key;
   snapshot.m15_last_swing_low = g_last_confirmed_m15_swing_low;
   snapshot.m15_last_swing_low_time = g_last_confirmed_m15_swing_low_time;
   snapshot.m15_last_swing_low_confirmation_key = g_last_confirmed_m15_swing_low_key;
   snapshot.m15_structure_break = CurrentM15StructureBreak(snapshot.m15_close);
   snapshot.valid = g_h1_slope_state.valid &&
                    IsFinitePositive(snapshot.d1_close) && IsFinitePositive(snapshot.d1_ema20) && IsFinitePositive(snapshot.d1_ema50) &&
                    IsFinitePositive(snapshot.h4_close) && IsFinitePositive(snapshot.h4_ema20) && IsFinitePositive(snapshot.h4_ema50);
   return snapshot.valid;
  }

bool TacticalM15Decidable(const SnapshotCore &snapshot)
  {
   return snapshot.m15_structure_break != "UNKNOWN" && snapshot.m15_structure_break != "AMBIGUOUS";
  }

string SnapshotInvalidDetail(const SnapshotCore &snapshot, const bool require_tactical_m15 = false)
  {
   string missing = "";
   for(int i = 0; i < AUDIT_TF_COUNT; i++)
     {
      if(!g_bar_availability[i].observed)
         missing += (missing == "" ? "" : ",") + g_timeframe_names[i] + "_bar_unobserved";
     }
   if(missing != "")
      return missing;
   if(!g_h1_slope_state.valid)
      missing += (missing == "" ? "" : ",") + "h1_q80_or_slope_invalid";
   if(!IsFinitePositive(snapshot.d1_close))
      missing += (missing == "" ? "" : ",") + "d1_close_invalid";
   if(!IsFinitePositive(snapshot.d1_ema20) || !IsFinitePositive(snapshot.d1_ema50))
      missing += (missing == "" ? "" : ",") + "d1_ema_invalid";
   if(!IsFinitePositive(snapshot.h4_close))
      missing += (missing == "" ? "" : ",") + "h4_close_invalid";
   if(!IsFinitePositive(snapshot.h4_ema20) || !IsFinitePositive(snapshot.h4_ema50))
      missing += (missing == "" ? "" : ",") + "h4_ema_invalid";
   if(require_tactical_m15 && !TacticalM15Decidable(snapshot))
     {
      missing += (missing == "" ? "" : ",") +
                 "m15_structure_" + snapshot.m15_structure_break +
                 "[close=" + DoubleToString(snapshot.m15_close, _Digits) +
                 ",high=" + DoubleToString(snapshot.m15_last_swing_high, _Digits) +
                 ",low=" + DoubleToString(snapshot.m15_last_swing_low, _Digits) + "]";
     }
   return missing == "" ? "snapshot_invalid_without_identified_field" : missing;
  }

bool H4ExpectedStack(const SnapshotCore &snapshot, const string expected_regime)
  {
   if(expected_regime == "UPTREND")
      return snapshot.h4_close > snapshot.h4_ema20 && snapshot.h4_ema20 > snapshot.h4_ema50 &&
             snapshot.h4_ema20_slope_5 >= 0.0 && snapshot.h4_ema50_slope_5 >= 0.0;
   return snapshot.h4_close < snapshot.h4_ema20 && snapshot.h4_ema20 < snapshot.h4_ema50 &&
          snapshot.h4_ema20_slope_5 <= 0.0 && snapshot.h4_ema50_slope_5 <= 0.0;
  }

void WriteFeature(const string stage, const int trade_index, const AuditEventKey &event_key, const SnapshotCore &snapshot)
  {
   if(g_feature_handle == INVALID_HANDLE || trade_index < 0 || trade_index >= ArraySize(g_trades))
      return;
   const VirtualTrade trade = g_trades[trade_index];
   FileWrite(
      g_feature_handle,
      AUDIT_SCHEMA_VERSION,
      InpRunId,
      stage,
      IntegerToString(event_key.tester_time_msc),
      IntegerToString(event_key.callback_sequence),
      IntegerToString(event_key.event_sequence),
      CurrentBrokerTimestamp(),
      trade.source_id,
      trade.component,
      trade.trade_id,
      trade.direction,
      trade.expected_regime,
      IntegerToString(snapshot.minimum_bar_shift),
      snapshot.router_state,
      EventKeyText(snapshot.availability[AUDIT_TF_D1].observation_key),
      DoubleToString(snapshot.d1_close, _Digits),
      DoubleToString(snapshot.d1_ema20, _Digits),
      DoubleToString(snapshot.d1_ema50, _Digits),
      DoubleToString(snapshot.d1_ema20_slope_5, 10),
      DoubleToString(snapshot.d1_ema50_slope_5, 10),
      snapshot.d1_structural_direction,
      EventKeyText(snapshot.availability[AUDIT_TF_H4].observation_key),
      DoubleToString(snapshot.h4_close, _Digits),
      DoubleToString(snapshot.h4_ema20, _Digits),
      DoubleToString(snapshot.h4_ema50, _Digits),
      DoubleToString(snapshot.h4_ema20_slope_5, 10),
      DoubleToString(snapshot.h4_ema50_slope_5, 10),
      snapshot.h4_structural_direction,
      BoolText(H4ExpectedStack(snapshot, trade.expected_regime)),
      EventKeyText(snapshot.availability[AUDIT_TF_H1].observation_key),
      DoubleToString(snapshot.h1.close, _Digits),
      DoubleToString(snapshot.h1.ema20, _Digits),
      DoubleToString(snapshot.h1.ema50, _Digits),
      DoubleToString(snapshot.h1.ema20_slope_5_price, 10),
      DoubleToString(snapshot.h1.ema50_slope_5_price, 10),
      DoubleToString(snapshot.h1.ema20_slope_5_norm, 10),
      DoubleToString(snapshot.h1.abs_slope_q80, 10),
      DoubleToString(snapshot.h1.previous_close, _Digits),
      DoubleToString(snapshot.h1.previous_ema50, _Digits),
      DoubleToString(snapshot.h1.previous_ema20_slope_5_norm, 10),
      DoubleToString(snapshot.h1.previous_abs_slope_q80, 10),
      EventKeyText(snapshot.availability[AUDIT_TF_M15].observation_key),
      DoubleToString(snapshot.m15_close, _Digits),
      DoubleToString(snapshot.m15_last_swing_high, _Digits),
      BrokerTimestamp(snapshot.m15_last_swing_high_time),
      EventKeyText(snapshot.m15_last_swing_high_confirmation_key),
      DoubleToString(snapshot.m15_last_swing_low, _Digits),
      BrokerTimestamp(snapshot.m15_last_swing_low_time),
      EventKeyText(snapshot.m15_last_swing_low_confirmation_key),
      snapshot.m15_structure_break,
      EventKeyText(snapshot.availability[AUDIT_TF_M5].observation_key),
      trade.signal_reason,
      DoubleToString(g_current_tick.bid, _Digits),
      DoubleToString(g_current_tick.ask, _Digits),
      IntegerToString((int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD)),
      DoubleToString(trade.initial_risk_usd, 10),
      DoubleToString(trade.original_sl, _Digits),
      DoubleToString(trade.original_tp, _Digits)
   );
  }

double ExecutableMark(const VirtualTrade &trade, const MqlTick &tick)
  {
   return trade.direction == "LONG" ? tick.bid : tick.ask;
  }

bool MarkReturnR(const VirtualTrade &trade, const double mark, double &return_r)
  {
   if(!IsFinitePositive(trade.initial_risk_usd) || !IsFinitePositive(mark))
      return false;
   const ENUM_ORDER_TYPE calculation_type = trade.direction == "LONG" ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double mark_pnl_usd = 0.0;
   if(!OrderCalcProfit(calculation_type, InpTargetSymbol, trade.executed_volume, trade.actual_entry_price, mark, mark_pnl_usd))
      return false;
   return_r = mark_pnl_usd / trade.initial_risk_usd;
   return MathIsValidNumber(return_r);
  }

bool CalculateInitialRisk(VirtualTrade &trade)
  {
   const ENUM_ORDER_TYPE calculation_type = trade.direction == "LONG" ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double risk = 0.0;
   if(!OrderCalcProfit(
      calculation_type,
      InpTargetSymbol,
      trade.executed_volume,
      trade.actual_entry_price,
      trade.original_sl,
      risk
   ))
      return false;
   trade.initial_risk_usd = MathAbs(risk);
   const double tick_size = SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_SIZE);
   const double tick_value_loss = SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(!IsFinitePositive(tick_size) || !IsFinitePositive(tick_value_loss))
      return false;
   trade.independent_initial_risk_usd =
      MathAbs(trade.actual_entry_price - trade.original_sl) / tick_size * tick_value_loss * trade.executed_volume;
   if(!IsFinitePositive(trade.initial_risk_usd) || !IsFinitePositive(trade.independent_initial_risk_usd))
      return false;
   return MathAbs(trade.initial_risk_usd - trade.independent_initial_risk_usd) < 0.005;
  }

void AddActiveTrade(const int trade_index)
  {
   const int size = ArraySize(g_active_trade_indices);
   ArrayResize(g_active_trade_indices, size + 1);
   g_active_trade_indices[size] = trade_index;
  }

void RemoveActiveTradeAt(const int active_position)
  {
   const int size = ArraySize(g_active_trade_indices);
   for(int i = active_position; i < size - 1; i++)
      g_active_trade_indices[i] = g_active_trade_indices[i + 1];
   ArrayResize(g_active_trade_indices, MathMax(0, size - 1));
  }

bool ExitTriggerReached(const VirtualTrade &trade, const MqlTick &tick)
  {
   if(!g_trade_session_open)
      return false;
   if(trade.native_exit_reason_code == (int)DEAL_REASON_SL)
     {
      if(trade.direction == "LONG")
         return tick.bid <= trade.original_sl;
      return tick.ask >= trade.original_sl;
     }
   if(trade.native_exit_reason_code == (int)DEAL_REASON_TP)
     {
      if(trade.direction == "LONG")
         return tick.bid >= trade.original_tp;
      return tick.ask <= trade.original_tp;
     }
   return false;
  }

bool CurrentTickIsStrictlyAfterEntry(const VirtualTrade &trade)
  {
   if(!trade.entry_emitted)
      return false;
   if(g_current_tick_time_msc > trade.entry_event_key.tester_time_msc)
      return true;
   if(g_current_tick_time_msc < trade.entry_event_key.tester_time_msc)
      return false;
   return g_callback_sequence > trade.entry_event_key.callback_sequence;
  }

void ProcessVirtualExits(const MqlTick &tick)
  {
   int active_position = 0;
   while(active_position < ArraySize(g_active_trade_indices))
     {
      const int trade_index = g_active_trade_indices[active_position];
      VirtualTrade trade = g_trades[trade_index];
      const bool trigger = ExitTriggerReached(trade, tick);
      if(trigger && tick.time < trade.exit_time_broker)
        {
         if(trade.early_exit_trigger_seen)
           {
            active_position++;
            continue;
           }
         trade.early_exit_trigger_seen = true;
         trade.failed = true;
         g_trades[trade_index] = trade;
         RuntimeFailure("virtual_exit_not_early", trade.trade_id, trade_index);
         active_position++;
         continue;
        }
      if(trigger && tick.time == trade.exit_time_broker)
        {
         const double mark = ExecutableMark(trade, tick);
         double unrealized_r = 0.0;
         if(!MarkReturnR(trade, mark, unrealized_r))
           {
            trade.failed = true;
            g_trades[trade_index] = trade;
            RuntimeFailure("exit_mark_calculation", trade.trade_id, trade_index);
           }
         const AuditEventKey key = WriteEvent(
            "EXIT", trade_index, "", 0, false, mark, unrealized_r, trade.mfe_r, trade.mae_r,
            trade.failed ? "FAIL" : "PASS", "virtual_first_sl_tp_trigger"
         );
         trade.exit_event_key = key;
         trade.exit_emitted = true;
         trade.active = false;
         g_exit_events++;
         g_trades[trade_index] = trade;
         if(g_have_last_completed_h1_snapshot)
            WriteFeature("EXIT", trade_index, key, g_last_completed_h1_snapshot);
         else
            RuntimeFailure("exit_snapshot_available", trade.trade_id, trade_index);
         RemoveActiveTradeAt(active_position);
         continue;
        }
      if(tick.time > trade.exit_time_broker)
        {
         trade.failed = true;
         trade.active = false;
         g_trades[trade_index] = trade;
         RuntimeFailure("virtual_exit_timestamp_reconciles", trade.trade_id, trade_index);
         RemoveActiveTradeAt(active_position);
         continue;
        }
      active_position++;
     }
  }

void ProcessScheduledSignalsAndEntries(const MqlTick &tick, const bool new_m5_bar)
  {
   while(g_next_signal_index < ArraySize(g_trades))
     {
      const int trade_index = g_next_signal_index;
      VirtualTrade trade = g_trades[trade_index];
      if(tick.time < trade.signal_time_broker || (tick.time == trade.signal_time_broker && !new_m5_bar))
         break;
      if(tick.time > trade.signal_time_broker)
        {
         trade.failed = true;
         trade.signal_emitted = true;
         g_trades[trade_index] = trade;
         RuntimeFailure("signal_timestamp_observed", trade.trade_id, trade_index);
        }
      else
        {
         SnapshotCore snapshot;
         const bool snapshot_core_valid = BuildSnapshotCore(snapshot);
         if(!snapshot_core_valid || !TacticalM15Decidable(snapshot))
           {
            trade.failed = true;
            g_trades[trade_index] = trade;
            RuntimeFailure(
               "signal_snapshot_complete",
               trade.trade_id + "|" + SnapshotInvalidDetail(snapshot, true),
               trade_index
            );
           }
         const AuditEventKey key = WriteEvent(
            "SIGNAL", trade_index, "M5", g_bar_availability[AUDIT_TF_M5].completed_bar_open, false,
            ExecutableMark(trade, tick), 0.0, 0.0, 0.0, trade.failed ? "FAIL" : "PASS", trade.signal_reason
         );
         trade.signal_event_key = key;
         trade.signal_emitted = true;
         g_signal_events++;
         g_trades[trade_index] = trade;
         if(snapshot_core_valid)
            WriteFeature("SIGNAL", trade_index, key, snapshot);
        }
      g_trades[trade_index] = trade;
      g_next_signal_index++;
     }

   while(g_next_entry_index < ArraySize(g_trades))
     {
      const int trade_index = g_next_entry_index;
      VirtualTrade trade = g_trades[trade_index];
      if(tick.time < trade.entry_time_broker || (tick.time == trade.entry_time_broker && !new_m5_bar))
         break;
      if(tick.time > trade.entry_time_broker)
        {
         trade.failed = true;
         trade.entry_emitted = true;
         g_trades[trade_index] = trade;
         RuntimeFailure("entry_timestamp_observed", trade.trade_id, trade_index);
        }
      else
        {
         if(!trade.signal_emitted)
           {
            trade.failed = true;
            g_trades[trade_index] = trade;
            RuntimeFailure("signal_precedes_entry", trade.trade_id, trade_index);
           }
         if(!CalculateInitialRisk(trade))
           {
            trade.failed = true;
            g_trades[trade_index] = trade;
            RuntimeFailure("initial_risk_reconciles_to_cent", trade.trade_id, trade_index);
           }
         g_trades[trade_index] = trade;
         SnapshotCore snapshot;
         const bool snapshot_core_valid = BuildSnapshotCore(snapshot);
         if(!snapshot_core_valid || !TacticalM15Decidable(snapshot))
           {
            trade.failed = true;
            g_trades[trade_index] = trade;
            RuntimeFailure(
               "entry_snapshot_complete",
               trade.trade_id + "|" + SnapshotInvalidDetail(snapshot, true),
               trade_index
            );
           }
         const AuditEventKey key = WriteEvent(
            "ENTRY", trade_index, "M5", g_bar_availability[AUDIT_TF_M5].completed_bar_open, true,
            ExecutableMark(trade, tick), 0.0, 0.0, 0.0, trade.failed ? "FAIL" : "PASS", "virtual_position_opened"
         );
         trade.entry_event_key = key;
         trade.entry_emitted = true;
         trade.active = !trade.failed;
         trade.mfe_r = 0.0;
         trade.mae_r = 0.0;
         g_entry_events++;
         g_trades[trade_index] = trade;
         if(snapshot_core_valid)
            WriteFeature("ENTRY", trade_index, key, snapshot);
         if(trade.active)
            AddActiveTrade(trade_index);
        }
      g_trades[trade_index] = trade;
      g_next_entry_index++;
     }
  }

void LogH1HoldingObservations(const MqlTick &tick)
  {
   if(!g_have_last_completed_h1_snapshot)
      return;
   for(int active_position = 0; active_position < ArraySize(g_active_trade_indices); active_position++)
     {
      const int trade_index = g_active_trade_indices[active_position];
      VirtualTrade trade = g_trades[trade_index];
      if(!trade.active || !CurrentTickIsStrictlyAfterEntry(trade))
         continue;
      const double mark = ExecutableMark(trade, tick);
      double unrealized_r = 0.0;
      if(!MarkReturnR(trade, mark, unrealized_r))
        {
         trade.failed = true;
         g_trades[trade_index] = trade;
         RuntimeFailure("h1_mark_calculation", trade.trade_id, trade_index);
         continue;
        }
      trade.holding_h1_bars++;
      g_trades[trade_index] = trade;
      const AuditEventKey key = WriteEvent(
         "H1_HOLD", trade_index, "H1", g_bar_availability[AUDIT_TF_H1].completed_bar_open, true,
         mark, unrealized_r, trade.mfe_r, trade.mae_r, trade.failed ? "FAIL" : "PASS",
         trade.failed ? "path_already_invalid" :
         (g_trade_session_open ? "completed_h1_first_actual_tick" : "completed_h1_first_actual_tick|trade_session_closed_quote_mark")
      );
      WriteFeature("H1_HOLD", trade_index, key, g_last_completed_h1_snapshot);
      g_h1_hold_events++;
     }
  }

void UpdateOpenTradeExtrema(const MqlTick &tick)
  {
   for(int active_position = 0; active_position < ArraySize(g_active_trade_indices); active_position++)
     {
      const int trade_index = g_active_trade_indices[active_position];
      VirtualTrade trade = g_trades[trade_index];
      if(!trade.active || !CurrentTickIsStrictlyAfterEntry(trade))
         continue;
      double mark_r = 0.0;
      if(!MarkReturnR(trade, ExecutableMark(trade, tick), mark_r))
        {
         trade.failed = true;
         g_trades[trade_index] = trade;
         RuntimeFailure("tick_mark_calculation", trade.trade_id, trade_index);
         continue;
        }
      if(mark_r > trade.mfe_r)
         trade.mfe_r = mark_r;
      if(mark_r < trade.mae_r)
         trade.mae_r = mark_r;
      g_trades[trade_index] = trade;
     }
  }

void WriteStaticProvenance()
  {
   WriteProvenance("audit_schema", AUDIT_SCHEMA_VERSION);
   WriteProvenance("authoritative_router_source_commit", AUDIT_SOURCE_COMMIT);
   WriteProvenance("authoritative_router_source_sha256", AUDIT_ROUTER_SOURCE_SHA256);
   WriteProvenance("terminal_build", IntegerToString((long)TerminalInfoInteger(TERMINAL_BUILD)));
   WriteProvenance("mql_tester", BoolText((bool)MQLInfoInteger(MQL_TESTER)));
   WriteProvenance("account_server", AccountInfoString(ACCOUNT_SERVER));
   WriteProvenance("account_login", IntegerToString((long)AccountInfoInteger(ACCOUNT_LOGIN)));
   WriteProvenance("account_currency", AccountInfoString(ACCOUNT_CURRENCY));
   WriteProvenance("symbol", InpTargetSymbol);
   WriteProvenance("symbol_digits", IntegerToString((long)SymbolInfoInteger(InpTargetSymbol, SYMBOL_DIGITS)));
   WriteProvenance("symbol_point", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT), 10));
   WriteProvenance("symbol_trade_tick_size", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_SIZE), 10));
   WriteProvenance("symbol_trade_tick_value_loss", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_VALUE_LOSS), 10));
   WriteProvenance("symbol_trade_contract_size", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_CONTRACT_SIZE), 10));
   WriteProvenance("symbol_volume_step", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP), 10));
   WriteProvenance("schedule_file", InpScheduleFileName);
   WriteProvenance("schedule_rows", IntegerToString(g_schedule_rows));
   WriteProvenance("bar_contract", "completed_shift_gte_1", "availability occurs on first actual modeled tick exposing shift 1");
   WriteProvenance("h1_q80_contract", "prior_252_type7_p80", "current bar excluded");
   WriteProvenance("m15_pivot_contract", "strict_2_left_2_right", "ties are not pivots");
   WriteProvenance(
      "tick_path_contract",
      "all_exact_modeled_bid_ask_ticks",
      "trade session gates SL/TP execution only; frozen MFE/MAE and H1 marks retain every modeled quote"
   );
   for(int i = 0; i < ArraySize(g_trade_sessions); i++)
     {
      const TradeSessionInterval session = g_trade_sessions[i];
      WriteProvenance(
         "trade_session",
         IntegerToString(session.day_of_week) + ":" +
         IntegerToString(session.from_seconds) + "-" + IntegerToString(session.to_seconds),
         "SymbolInfoSessionTrade"
      );
     }
  }

void WriteTimezoneProvenanceIfChanged()
  {
   MqlDateTime parts;
   TimeToStruct(g_current_tick.time, parts);
   const string day = StringFormat("%04d-%02d-%02d", parts.year, parts.mon, parts.day);
   const long broker_gmt_offset_seconds = (long)(TimeCurrent() - TimeGMT());
   if(!g_timezone_written || day != g_last_timezone_day || broker_gmt_offset_seconds != g_last_broker_gmt_offset_seconds)
     {
      WriteProvenance(
         "broker_to_gmt_offset_seconds",
         IntegerToString(broker_gmt_offset_seconds),
         "broker=" + BrokerTimestamp(TimeCurrent()) +
         ",trade_server=" + BrokerTimestamp(TimeTradeServer()) +
         ",gmt=" + BrokerTimestamp(TimeGMT()) +
         ",local=" + BrokerTimestamp(TimeLocal())
      );
      g_timezone_written = true;
      g_last_timezone_day = day;
      g_last_broker_gmt_offset_seconds = broker_gmt_offset_seconds;
     }
  }

void FinalizeAudit()
  {
   if(g_finalized)
      return;
   g_finalized = true;
   bool every_trade_complete = true;
   for(int i = 0; i < ArraySize(g_trades); i++)
     {
      if(!g_trades[i].signal_emitted || !g_trades[i].entry_emitted || !g_trades[i].exit_emitted || g_trades[i].failed)
        {
         every_trade_complete = false;
         break;
        }
     }
   WriteAssertion(
      "all_678_schedule_rows_complete",
      every_trade_complete && g_signal_events == InpExpectedScheduleRows &&
      g_entry_events == InpExpectedScheduleRows && g_exit_events == InpExpectedScheduleRows ? "PASS" : "FAIL",
      "signal=" + IntegerToString(g_signal_events) +
      ",entry=" + IntegerToString(g_entry_events) +
      ",exit=" + IntegerToString(g_exit_events) +
      ",h1_hold=" + IntegerToString(g_h1_hold_events)
   );
   WriteAssertion("zero_execution_surface_runtime", g_runtime_failed ? "FAIL" : "PASS", "virtual positions only");
   WriteProvenance("runtime_failed", BoolText(g_runtime_failed));
   if(g_event_handle != INVALID_HANDLE)
      FileFlush(g_event_handle);
   if(g_feature_handle != INVALID_HANDLE)
      FileFlush(g_feature_handle);
   if(g_provenance_handle != INVALID_HANDLE)
      FileFlush(g_provenance_handle);
   if(g_assertion_handle != INVALID_HANDLE)
      FileFlush(g_assertion_handle);
  }

int OnInit()
  {
   for(int i = 0; i < AUDIT_TF_COUNT; i++)
     {
      g_ema20_handles[i] = INVALID_HANDLE;
      g_ema50_handles[i] = INVALID_HANDLE;
      g_atr_handles[i] = INVALID_HANDLE;
      g_bar_availability[i].observed = false;
      g_bar_availability[i].observation_key = ZeroEventKey();
     }
   g_last_confirmed_m15_swing_high_key = ZeroEventKey();
   g_last_confirmed_m15_swing_low_key = ZeroEventKey();

   if(!OpenOutputLogs())
      return INIT_FAILED;
   if(!(bool)MQLInfoInteger(MQL_TESTER))
     {
      WriteAssertion("tester_only", "FAIL", "MQL_TESTER=false");
      CloseOutputLogs();
      return INIT_FAILED;
     }
   WriteAssertion("tester_only", "PASS", "MQL_TESTER=true");
   if(_Symbol != InpTargetSymbol || !SymbolSelect(InpTargetSymbol, true))
     {
      WriteAssertion("target_symbol", "FAIL", _Symbol + "!=" + InpTargetSymbol);
      CloseOutputLogs();
      return INIT_FAILED;
     }
   if(!FrozenInputsMatch())
     {
      WriteAssertion("frozen_router_inputs", "FAIL", "Router V1 input mismatch");
      CloseOutputLogs();
      return INIT_FAILED;
     }
   WriteAssertion("frozen_router_inputs", "PASS", "14/20/50/5/2/true/3/95/60/30/5/1");
   if(!LoadTradeSessions())
     {
      WriteAssertion("trade_sessions", "FAIL", "SymbolInfoSessionTrade unavailable");
      CloseOutputLogs();
      return INIT_FAILED;
     }
   WriteAssertion("trade_sessions", "PASS", "SymbolInfoSessionTrade intervals loaded");
   if(!InitializeIndicatorHandles())
     {
      WriteAssertion("indicator_handles", "FAIL", "one or more handles unavailable");
      ReleaseIndicatorHandles();
      CloseOutputLogs();
      return INIT_FAILED;
     }
   WriteAssertion("indicator_handles", "PASS", "D1/H4/H1/M15/M5 EMA20/EMA50/ATR14");
   if(!LoadSchedule())
     {
      ReleaseIndicatorHandles();
      CloseOutputLogs();
      return INIT_FAILED;
     }
   WriteStaticProvenance();
   return INIT_SUCCEEDED;
  }

void OnTick()
  {
   g_callback_sequence++;
   if(!SymbolInfoTick(InpTargetSymbol, g_current_tick))
     {
      RuntimeFailure("symbol_tick_available", InpTargetSymbol);
      return;
     }
   g_have_current_tick = true;
   g_current_tick_time_msc = g_current_tick.time_msc;
   g_trade_session_open = TradeSessionOpenAt(g_current_tick.time);
   if(g_current_tick_time_msc <= 0 ||
      (g_previous_tick_time_msc > 0 && g_current_tick_time_msc < g_previous_tick_time_msc))
     {
      RuntimeFailure("tester_tick_time_monotone", IntegerToString(g_current_tick_time_msc));
      return;
     }
   g_previous_tick_time_msc = g_current_tick_time_msc;

   // Existing virtual positions exit before this callback can make a new
   // completed-H1 observation eligible. This makes same-tick cases fail closed.
   ProcessVirtualExits(g_current_tick);

   const bool new_m5 = ObserveCompletedBar(AUDIT_TF_M5);
   bool new_d1 = false;
   bool new_h4 = false;
   bool new_h1 = false;
   bool new_m15 = false;
   // A newly observable higher-timeframe completed bar can only arrive on the
   // first tick of a new M5 bar.  Gate the four expensive iTime checks behind
   // that exact event without changing completed-bar availability semantics.
   if(new_m5)
     {
      new_d1 = ObserveCompletedBar(AUDIT_TF_D1);
      new_h4 = ObserveCompletedBar(AUDIT_TF_H4);
      new_h1 = ObserveCompletedBar(AUDIT_TF_H1);
      new_m15 = ObserveCompletedBar(AUDIT_TF_M15);
      WriteTimezoneProvenanceIfChanged();
     }
   if(new_d1 || new_h4 || new_m15)
     {
      // Named booleans intentionally preserve event-order provenance.
     }

   if(new_h1)
     {
      ComputeH1SlopeState(g_h1_slope_state);
      SnapshotCore snapshot;
      if(BuildSnapshotCore(snapshot))
        {
         g_last_completed_h1_snapshot = snapshot;
         g_have_last_completed_h1_snapshot = true;
         LogH1HoldingObservations(g_current_tick);
        }
      else
        {
         g_have_last_completed_h1_snapshot = false;
         const string detail =
            BrokerTimestamp(g_bar_availability[AUDIT_TF_H1].completed_bar_open) + "|" +
            SnapshotInvalidDetail(snapshot);
         if(ArraySize(g_active_trade_indices) == 0)
            WriteEvent(
               "SNAPSHOT_UNAVAILABLE", -1, "H1", g_bar_availability[AUDIT_TF_H1].completed_bar_open,
               false, 0.0, 0.0, 0.0, 0.0, "DIAGNOSTIC", detail
            );
         else
           {
            for(int active_position = 0; active_position < ArraySize(g_active_trade_indices); active_position++)
              {
               const int trade_index = g_active_trade_indices[active_position];
               VirtualTrade trade = g_trades[trade_index];
               trade.failed = true;
               g_trades[trade_index] = trade;
               RuntimeFailure("completed_h1_snapshot_complete", detail, trade_index);
              }
           }
        }
     }

   ProcessScheduledSignalsAndEntries(g_current_tick, new_m5);
   UpdateOpenTradeExtrema(g_current_tick);
  }

double OnTester()
  {
   FinalizeAudit();
   return 0.0;
  }

void OnDeinit(const int reason)
  {
   WriteProvenance("deinit_reason", IntegerToString(reason));
   FinalizeAudit();
   ReleaseIndicatorHandles();
   CloseOutputLogs();
  }
//+------------------------------------------------------------------+
