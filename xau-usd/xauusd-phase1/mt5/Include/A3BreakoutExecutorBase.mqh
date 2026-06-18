#ifndef A3_BREAKOUT_EXECUTOR_BASE_MQH
#define A3_BREAKOUT_EXECUTOR_BASE_MQH

#ifndef A3_BREAKOUT_DEFAULT_RUN_ID
#define A3_BREAKOUT_DEFAULT_RUN_ID "A3_BREAKOUT_BASE"
#endif
#ifndef A3_BREAKOUT_DEFAULT_MAGIC
#define A3_BREAKOUT_DEFAULT_MAGIC 933200
#endif
#ifndef A3_BREAKOUT_EXPECTED_MAGIC
#define A3_BREAKOUT_EXPECTED_MAGIC 933200
#endif
#ifndef A3_BREAKOUT_DEFAULT_COMMENT
#define A3_BREAKOUT_DEFAULT_COMMENT "A3_BREAKOUT"
#endif
#ifndef A3_BREAKOUT_SIGNAL_LOG
#define A3_BREAKOUT_SIGNAL_LOG "a3_breakout_signal_log.csv"
#endif
#ifndef A3_BREAKOUT_STARTUP_LOG
#define A3_BREAKOUT_STARTUP_LOG "a3_breakout_startup.csv"
#endif
#ifndef A3_BREAKOUT_ORDER_LOG
#define A3_BREAKOUT_ORDER_LOG "a3_breakout_order_log.csv"
#endif
#ifndef A3_BREAKOUT_MANAGEMENT_LOG
#define A3_BREAKOUT_MANAGEMENT_LOG "a3_breakout_management_log.csv"
#endif
#ifndef A3_BREAKOUT_ATTACHED_STATUS
#define A3_BREAKOUT_ATTACHED_STATUS "ATTACHED_A3_BREAKOUT"
#endif
#ifndef A3_BREAKOUT_TREND_GUARD_DEFAULT
#define A3_BREAKOUT_TREND_GUARD_DEFAULT false
#endif
#ifndef A3_BREAKOUT_EXIT_PROTECTION_DEFAULT
#define A3_BREAKOUT_EXIT_PROTECTION_DEFAULT false
#endif
#ifndef A3_BREAKOUT_SESSION_GATE_DEFAULT
#define A3_BREAKOUT_SESSION_GATE_DEFAULT false
#endif
#ifndef A3_BREAKOUT_STOP_FLOOR_DEFAULT
#define A3_BREAKOUT_STOP_FLOOR_DEFAULT false
#endif
#ifndef A3_BREAKOUT_TREND_SHADOW_DEFAULT
#define A3_BREAKOUT_TREND_SHADOW_DEFAULT false
#endif
#ifndef A3_BREAKOUT_SOFT_RETEST_DEFAULT
#define A3_BREAKOUT_SOFT_RETEST_DEFAULT false
#endif

#include <Phase1/Phase1Types.mqh>
#include <Phase1/Phase1BreakoutRetest.mqh>
#include <DirectionStateShadow.mqh>

input string InpRunId = A3_BREAKOUT_DEFAULT_RUN_ID;
input bool InpDryRunOnly = true;
input bool InpBrokerActionAllowed = false;
input string InpTargetSymbol = "XAUUSD";
input string InpExpectedServerMarker = "Demo";
input string InpAllowedAccountLoginsCsv = "1033669";
input string InpExecutionKillSwitchFileName = "A3_EXECUTION_KILL.txt";
input string InpFullStopFileName = "A3_FULL_STOP.txt";
input int InpMagicNumber = A3_BREAKOUT_DEFAULT_MAGIC;
input string InpOrderComment = A3_BREAKOUT_DEFAULT_COMMENT;
input string InpSignalLogFileName = A3_BREAKOUT_SIGNAL_LOG;
input string InpStartupLogFileName = A3_BREAKOUT_STARTUP_LOG;
input string InpOrderLogFileName = A3_BREAKOUT_ORDER_LOG;
input string InpManagementLogFileName = A3_BREAKOUT_MANAGEMENT_LOG;
input string InpDirectionStateFileName = "dirstate_xauusd.csv";
input int InpMaxOpenPositionsPerMagic = 1;
input double InpMaxEstimatedCostR = 0.15;
input double InpCostWarnR = 0.20;
input double InpAbsoluteRejectCostR = 0.30;
input double InpMaxMeasuredSpreadPoints = 75.0;
input bool InpTradeSessionGateEnabled = A3_BREAKOUT_SESSION_GATE_DEFAULT;
input int InpTradeSessionStartHour = 12;
input int InpTradeSessionEndHour = 15;
input int InpMinSecondsBetweenOrders = 60;
input double InpFixedLot = 0.01;
input int InpDeviationPoints = 50;
input bool InpXauStopDistanceFloorEnabled = A3_BREAKOUT_STOP_FLOOR_DEFAULT;
input bool InpTrendGuardEnabled = A3_BREAKOUT_TREND_GUARD_DEFAULT;
input bool InpTrendGuardShadowOnly = A3_BREAKOUT_TREND_SHADOW_DEFAULT;
input int InpTrendH1LookbackBars = 12;
input int InpTrendH4LookbackBars = 6;
input double InpTrendMinMovePoints = 100.0;
input bool InpSoftRetestFilterEnabled = A3_BREAKOUT_SOFT_RETEST_DEFAULT;
input int InpSoftRetestMaxBarsAfterBreak = 15;
input double InpSoftRetestMinBodyToRange = 0.45;
input double InpSoftRetestMinDirectionalCloseLocation = 0.60;
input double InpSoftRetestRetestCloseMarginAtr = 0.05;
input bool InpBreakevenEnabled = A3_BREAKOUT_EXIT_PROTECTION_DEFAULT;
input double InpBreakevenTriggerR = 0.50;
input bool InpPartialTakeProfitEnabled = A3_BREAKOUT_EXIT_PROTECTION_DEFAULT;
input double InpPartialTriggerR = 1.00;
input double InpPartialCloseFraction = 0.50;

CPhase1BreakoutRetestObserver g_breakout_observer;
datetime g_last_m5_bar_time = 0;
datetime g_last_order_submit_time = 0;

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

bool KillSwitchFileContainsKill(const string file_name)
{
   if(!FileIsExist(file_name))
      return false;
   int handle = FileOpen(file_name, FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE);
   if(handle == INVALID_HANDLE)
      return false;
   string content = "";
   while(!FileIsEnding(handle))
      content += " " + FileReadString(handle);
   FileClose(handle);
   return ContainsText(content, "KILL");
}

bool FullStopActive()
{
   return KillSwitchFileContainsKill(InpFullStopFileName);
}

bool ExecutionKillSwitchActive()
{
   return KillSwitchFileContainsKill(InpExecutionKillSwitchFileName);
}

bool AccountLoginWhitelisted()
{
   return CsvContainsTextToken(InpAllowedAccountLoginsCsv, IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN)));
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

bool ScopeLocksPass(string &guard_reason)
{
   if(_Symbol != "XAUUSD" || InpTargetSymbol != "XAUUSD")
   {
      guard_reason = "SCOPE_LOCK_SYMBOL_BLOCK";
      return false;
   }
   string server = AccountInfoString(ACCOUNT_SERVER);
   if(server == "" || !ContainsText(server, InpExpectedServerMarker) || ContainsText(server, "live") || ContainsText(server, "real"))
   {
      guard_reason = "SCOPE_LOCK_DEMO_SERVER_BLOCK";
      return false;
   }
   if(!AccountLoginWhitelisted())
   {
      guard_reason = "SCOPE_LOCK_LOGIN_BLOCK";
      return false;
   }
   if(FullStopActive())
   {
      guard_reason = "SCOPE_LOCK_FULL_STOP_BLOCK";
      return false;
   }
   guard_reason = "PASS";
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
      "trade_session_gate_enabled",
      "trade_session_start_hour",
      "trade_session_end_hour",
      "min_seconds_between_orders",
      "xau_stop_distance_floor_enabled",
      "execution_kill_switch_file",
      "full_stop_file",
      "trend_guard_enabled",
      "trend_guard_shadow_only",
      "soft_retest_filter_enabled",
      "soft_retest_max_bars_after_break",
      "soft_retest_min_body_to_range",
      "soft_retest_min_directional_close_location",
      "soft_retest_retest_close_margin_atr",
      "breakeven_enabled",
      "partial_take_profit_enabled",
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
      "estimated_cost_R",
      "cost_warn",
      "open_positions_for_magic",
      "trend_guard_enabled",
      "h1_trend",
      "h4_trend",
      "trend_guard_reason",
      "trend_shadow_enabled",
      "trend_shadow_pass",
      "trend_shadow_reason",
      "breakeven_enabled",
      "partial_take_profit_enabled",
      "dry_run",
      "broker_action_allowed",
      "dirstate_direction",
      "dirstate_regime",
      "dirstate_strength"
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
      "magic",
      "comment",
      "action",
      "position_ticket",
      "position_type",
      "position_volume",
      "request_volume",
      "open_price",
      "request_price",
      "current_sl",
      "new_sl",
      "tp",
      "trigger_r",
      "retcode",
      "retcode_description",
      "reason"
   };
   return AppendCsvRow(InpManagementLogFileName, header);
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
      BoolText(InpTradeSessionGateEnabled),
      IntegerToString(InpTradeSessionStartHour),
      IntegerToString(InpTradeSessionEndHour),
      IntegerToString(InpMinSecondsBetweenOrders),
      BoolText(InpXauStopDistanceFloorEnabled),
      InpExecutionKillSwitchFileName,
      InpFullStopFileName,
      BoolText(InpTrendGuardEnabled),
      BoolText(InpTrendGuardShadowOnly),
      BoolText(InpSoftRetestFilterEnabled),
      IntegerToString(InpSoftRetestMaxBarsAfterBreak),
      DoubleToString(InpSoftRetestMinBodyToRange, 2),
      DoubleToString(InpSoftRetestMinDirectionalCloseLocation, 2),
      DoubleToString(InpSoftRetestRetestCloseMarginAtr, 2),
      BoolText(InpBreakevenEnabled),
      BoolText(InpPartialTakeProfitEnabled),
      status_text
   };
   return AppendCsvRow(InpStartupLogFileName, row);
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

double NormalizePartialVolume(const double requested)
{
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double volume = requested;
   if(step > 0.0)
      volume = MathFloor(volume / step) * step;
   int digits = 2;
   if(step > 0.0 && step < 0.01)
      digits = 3;
   if(step > 0.0 && step < 0.001)
      digits = 4;
   return NormalizeDouble(volume, digits);
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

int TrendDirection(const ENUM_TIMEFRAMES timeframe, const int lookback_bars)
{
   if(lookback_bars < 2 || Bars(_Symbol, timeframe) <= lookback_bars + 2)
      return 0;
   double recent = iClose(_Symbol, timeframe, 1);
   double past = iClose(_Symbol, timeframe, lookback_bars + 1);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(recent <= 0.0 || past <= 0.0 || point <= 0.0)
      return 0;
   double delta_points = (recent - past) / point;
   if(delta_points >= InpTrendMinMovePoints)
      return 1;
   if(delta_points <= -InpTrendMinMovePoints)
      return -1;
   return 0;
}

string TrendText(const int trend)
{
   if(trend > 0)
      return "UP";
   if(trend < 0)
      return "DOWN";
   return "NEUTRAL";
}

double AverageM5RangePrice(const int start_shift, const int periods)
{
   double total = 0.0;
   int counted = 0;
   for(int shift = start_shift; shift < start_shift + periods; shift++)
   {
      double high_price = iHigh(_Symbol, PERIOD_M5, shift);
      double low_price = iLow(_Symbol, PERIOD_M5, shift);
      if(high_price <= 0.0 || low_price <= 0.0 || high_price < low_price)
         continue;
      total += high_price - low_price;
      counted++;
   }
   if(counted <= 0)
      return 0.0;
   return total / counted;
}

void BlockSoftRetestObservation(Phase1BreakoutRetestObservation &observation, const string reason_code)
{
   observation.would_signal = false;
   observation.stage = "SOFT_RETEST_FILTER_BLOCK";
   observation.reason_code = reason_code;
}

bool ApplySoftRetestFilter(Phase1BreakoutRetestObservation &observation)
{
   if(!InpSoftRetestFilterEnabled || !observation.would_signal)
      return true;

   bool is_long = observation.direction_text == "LONG";
   bool is_short = observation.direction_text == "SHORT";
   if(!is_long && !is_short)
   {
      BlockSoftRetestObservation(observation, "SOFT_RETEST_NO_DIRECTION");
      return false;
   }

   int bars_after_break = observation.break_shift - 2;
   if(bars_after_break < 1 || bars_after_break > InpSoftRetestMaxBarsAfterBreak)
   {
      BlockSoftRetestObservation(observation, "SOFT_RETEST_BARS_AFTER_BREAK_BLOCK");
      return false;
   }

   double retest_atr = AverageM5RangePrice(2, 14);
   if(retest_atr <= 0.0)
   {
      BlockSoftRetestObservation(observation, "SOFT_RETEST_ATR_UNAVAILABLE");
      return false;
   }

   double retest_close = iClose(_Symbol, PERIOD_M5, 2);
   double confirmation_open = iOpen(_Symbol, PERIOD_M5, 1);
   double confirmation_high = iHigh(_Symbol, PERIOD_M5, 1);
   double confirmation_low = iLow(_Symbol, PERIOD_M5, 1);
   double confirmation_close = iClose(_Symbol, PERIOD_M5, 1);
   if(retest_close <= 0.0 || confirmation_open <= 0.0 || confirmation_high <= 0.0 || confirmation_low <= 0.0 || confirmation_close <= 0.0)
   {
      BlockSoftRetestObservation(observation, "SOFT_RETEST_BAR_DATA_UNAVAILABLE");
      return false;
   }

   double level = observation.level_price;
   double margin = InpSoftRetestRetestCloseMarginAtr * retest_atr;
   if(is_long)
   {
      if(retest_close < level + margin)
      {
         BlockSoftRetestObservation(observation, "SOFT_RETEST_RETEST_MARGIN_BLOCK");
         return false;
      }
      if(confirmation_close <= level)
      {
         BlockSoftRetestObservation(observation, "SOFT_RETEST_CONFIRMATION_CLOSE_BLOCK");
         return false;
      }
   }
   else
   {
      if(retest_close > level - margin)
      {
         BlockSoftRetestObservation(observation, "SOFT_RETEST_RETEST_MARGIN_BLOCK");
         return false;
      }
      if(confirmation_close >= level)
      {
         BlockSoftRetestObservation(observation, "SOFT_RETEST_CONFIRMATION_CLOSE_BLOCK");
         return false;
      }
   }

   double range = confirmation_high - confirmation_low;
   if(range <= 0.0)
   {
      BlockSoftRetestObservation(observation, "SOFT_RETEST_CONFIRMATION_RANGE_BLOCK");
      return false;
   }

   double body_to_range = MathAbs(confirmation_close - confirmation_open) / range;
   if(body_to_range < InpSoftRetestMinBodyToRange)
   {
      BlockSoftRetestObservation(observation, "SOFT_RETEST_BODY_BLOCK");
      return false;
   }

   double close_location = (confirmation_close - confirmation_low) / range;
   if(is_long && close_location < InpSoftRetestMinDirectionalCloseLocation)
   {
      BlockSoftRetestObservation(observation, "SOFT_RETEST_DIRECTIONAL_CLOSE_BLOCK");
      return false;
   }
   if(is_short && close_location > 1.0 - InpSoftRetestMinDirectionalCloseLocation)
   {
      BlockSoftRetestObservation(observation, "SOFT_RETEST_DIRECTIONAL_CLOSE_BLOCK");
      return false;
   }

   observation.stage = "SOFT_RETEST_WOULD_SIGNAL";
   observation.reason_code = observation.reason_code + "_SOFT_RETEST_V2";
   return true;
}

int SignalDirectionCode(const Phase1BreakoutRetestObservation &observation)
{
   if(observation.direction_text == "LONG")
      return 1;
   if(observation.direction_text == "SHORT")
      return -1;
   return 0;
}

bool TrendGuardDecision(const Phase1BreakoutRetestObservation &observation, const int h1_trend, const int h4_trend, string &trend_reason)
{
   if(!observation.would_signal)
   {
      trend_reason = "NO_SIGNAL";
      return false;
   }
   int signal_direction = SignalDirectionCode(observation);
   if(signal_direction == 0)
   {
      trend_reason = "NO_SIGNAL_DIRECTION";
      return false;
   }
   if(h1_trend == -signal_direction || h4_trend == -signal_direction)
   {
      trend_reason = "TREND_AGAINST_SIGNAL";
      return false;
   }
   trend_reason = "TREND_PASS";
   return true;
}

bool TrendGuardPass(const Phase1BreakoutRetestObservation &observation, const int h1_trend, const int h4_trend, string &trend_reason)
{
   if(!InpTrendGuardEnabled)
   {
      trend_reason = "TREND_GUARD_DISABLED";
      return true;
   }
   return TrendGuardDecision(observation, h1_trend, h4_trend, trend_reason);
}

bool TradingGuardsPass(
   const Phase1BreakoutRetestObservation &observation,
   const double spread_points,
   const double estimated_cost_r,
   const int h1_trend,
   const int h4_trend,
   string &guard_reason,
   string &trend_reason
)
{
   if(!observation.would_signal)
   {
      guard_reason = "NO_SIGNAL";
      trend_reason = "NO_SIGNAL";
      return false;
   }
   if(!ScopeLocksPass(guard_reason))
      return false;
   if(ExecutionKillSwitchActive())
   {
      guard_reason = "EXECUTION_KILL_SWITCH_BLOCK";
      return false;
   }
   if(InpDryRunOnly || !InpBrokerActionAllowed)
   {
      guard_reason = "ARMING_DISABLED";
      return false;
   }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
   {
      guard_reason = "TERMINAL_OR_ACCOUNT_TRADING_DISABLED";
      return false;
   }
   if(!ServerHourInTradeSession())
   {
      guard_reason = "SERVER_HOUR_SESSION_GATE";
      return false;
   }
   if(observation.entry_price <= 0.0 || observation.stop_loss <= 0.0 || observation.take_profit <= 0.0)
   {
      guard_reason = "MISSING_ENTRY_SL_TP";
      return false;
   }
   if(CountOpenPositionsForMagic() >= InpMaxOpenPositionsPerMagic)
   {
      guard_reason = "MAGIC_POSITION_CAP_BLOCK";
      return false;
   }
   if(InpMaxMeasuredSpreadPoints > 0.0 && spread_points > InpMaxMeasuredSpreadPoints)
   {
      guard_reason = "SPREAD_CAP_BLOCK";
      return false;
   }
   if((InpAbsoluteRejectCostR > 0.0 && estimated_cost_r > InpAbsoluteRejectCostR)
      || (InpMaxEstimatedCostR > 0.0 && estimated_cost_r > InpMaxEstimatedCostR))
   {
      guard_reason = "COST_R_CAP_BLOCK";
      return false;
   }
   if(InpMinSecondsBetweenOrders > 0 && g_last_order_submit_time > 0 && TimeCurrent() - g_last_order_submit_time < InpMinSecondsBetweenOrders)
   {
      guard_reason = "MIN_SECONDS_BETWEEN_ORDERS";
      return false;
   }
   if(!TrendGuardPass(observation, h1_trend, h4_trend, trend_reason))
   {
      guard_reason = trend_reason;
      return false;
   }
   guard_reason = "PASS";
   return true;
}

void WriteOrderLogRow(
   const string action,
   const Phase1BreakoutRetestObservation &observation,
   const double volume,
   const double request_price,
   const double sl,
   const double tp,
   const MqlTradeResult &result,
   const string guard_reason,
   const double spread_points,
   const double estimated_cost_r,
   const double stop_distance_points
)
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   string dirstate_direction = "0";
   string dirstate_regime = "UNKNOWN";
   string dirstate_strength = "0.000";
   DirectionStateShadowFieldsForLog(dirstate_direction, dirstate_regime, dirstate_strength, InpDirectionStateFileName);
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
      dirstate_direction,
      dirstate_regime,
      dirstate_strength
   };
   AppendCsvRow(InpOrderLogFileName, row);
}

bool SendMarketOrder(const Phase1BreakoutRetestObservation &observation, const double spread_points, const double estimated_cost_r)
{
   MqlTradeResult result;
   ZeroMemory(result);
   if(ExecutionKillSwitchActive())
   {
      WriteOrderLogRow("GUARD_BLOCK", observation, 0.0, 0.0, 0.0, 0.0, result, "EXECUTION_KILL_SWITCH_BLOCK", spread_points, estimated_cost_r, observation.stop_distance_points);
      return false;
   }
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   bool is_long = observation.direction_text == "LONG";
   double price = is_long ? ask : bid;
   double signal_risk = MathAbs(observation.entry_price - observation.stop_loss);
   if(point <= 0.0 || signal_risk <= 0.0 || price <= 0.0)
   {
      WriteOrderLogRow("GUARD_BLOCK", observation, 0.0, price, 0.0, 0.0, result, "INVALID_PRICE_OR_RISK", spread_points, estimated_cost_r, observation.stop_distance_points);
      return false;
   }
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double sl = NormalizeDouble(is_long ? price - signal_risk : price + signal_risk, digits);
   double tp = NormalizeDouble(is_long ? price + 1.50 * signal_risk : price - 1.50 * signal_risk, digits);
   if(InpXauStopDistanceFloorEnabled)
   {
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
      sl = NormalizeDouble(is_long ? price - signal_risk : price + signal_risk, digits);
      tp = NormalizeDouble(is_long ? price + 1.50 * signal_risk : price - 1.50 * signal_risk, digits);
   }
   price = NormalizeDouble(price, digits);
   double stop_distance_points = point > 0.0 ? signal_risk / point : observation.stop_distance_points;
   double volume = NormalizeVolumeForSymbol(InpFixedLot);
   if(volume <= 0.0)
   {
      WriteOrderLogRow("GUARD_BLOCK", observation, 0.0, price, sl, tp, result, "INVALID_VOLUME", spread_points, estimated_cost_r, stop_distance_points);
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
   double executed_cost_r = signal_risk > 0.0 && point > 0.0 ? (CurrentSpreadPoints() * point / signal_risk) : estimated_cost_r;
   WriteOrderLogRow(action, observation, volume, price, sl, tp, result, "PASS", spread_points, executed_cost_r, stop_distance_points);
   return sent;
}

void WriteSignalRow(
   const Phase1BreakoutRetestObservation &observation,
   const double spread_points,
   const double estimated_cost_r,
   const string guard_reason,
   const bool guard_pass,
   const int h1_trend,
   const int h4_trend,
   const string trend_reason,
   const bool trend_shadow_pass,
   const string trend_shadow_reason
)
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   string dirstate_direction = "0";
   string dirstate_regime = "UNKNOWN";
   string dirstate_strength = "0.000";
   DirectionStateShadowFieldsForLog(dirstate_direction, dirstate_regime, dirstate_strength, InpDirectionStateFileName);
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
      TimeToString(iTime(_Symbol, PERIOD_M5, 0), TIME_DATE | TIME_SECONDS),
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
      DoubleToString(estimated_cost_r, 4),
      estimated_cost_r > InpCostWarnR ? "COST_WARN" : "",
      IntegerToString(CountOpenPositionsForMagic()),
      BoolText(InpTrendGuardEnabled),
      TrendText(h1_trend),
      TrendText(h4_trend),
      trend_reason,
      BoolText(InpTrendGuardShadowOnly),
      BoolText(trend_shadow_pass),
      trend_shadow_reason,
      BoolText(InpBreakevenEnabled),
      BoolText(InpPartialTakeProfitEnabled),
      BoolText(InpDryRunOnly),
      BoolText(InpBrokerActionAllowed),
      dirstate_direction,
      dirstate_regime,
      dirstate_strength
   };
   AppendCsvRow(InpSignalLogFileName, row);
}

string PositionActionStateName(const string prefix, const ulong ticket)
{
   return prefix + "_" + IntegerToString(InpMagicNumber) + "_" + IntegerToString((int)ticket);
}

double PositionFavorableR(const ENUM_POSITION_TYPE type, const double open_price, const double sl)
{
   double risk = MathAbs(open_price - sl);
   if(risk <= 0.0)
      return 0.0;
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   if(type == POSITION_TYPE_BUY)
      return (bid - open_price) / risk;
   return (open_price - ask) / risk;
}

void WriteManagementRow(
   const string action,
   const ulong ticket,
   const ENUM_POSITION_TYPE type,
   const double position_volume,
   const double request_volume,
   const double open_price,
   const double request_price,
   const double current_sl,
   const double new_sl,
   const double tp,
   const double trigger_r,
   const MqlTradeResult &result,
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
      IntegerToString(InpMagicNumber),
      InpOrderComment,
      action,
      IntegerToString((int)ticket),
      type == POSITION_TYPE_BUY ? "BUY" : "SELL",
      DoubleToString(position_volume, 2),
      DoubleToString(request_volume, 2),
      DoubleToString(open_price, digits),
      DoubleToString(request_price, digits),
      DoubleToString(current_sl, digits),
      DoubleToString(new_sl, digits),
      DoubleToString(tp, digits),
      DoubleToString(trigger_r, 4),
      IntegerToString((int)result.retcode),
      result.comment,
      reason
   };
   AppendCsvRow(InpManagementLogFileName, row);
}

bool MoveStopToBreakeven(const ulong ticket, const ENUM_POSITION_TYPE type, const double volume, const double open_price, const double current_sl, const double tp, const double trigger_r)
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double new_sl = NormalizeDouble(open_price, digits);
   bool already_protected = (type == POSITION_TYPE_BUY && current_sl >= new_sl) || (type == POSITION_TYPE_SELL && current_sl <= new_sl && current_sl > 0.0);
   if(already_protected)
      return false;

   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   if(ExecutionKillSwitchActive())
   {
      WriteManagementRow("BREAKEVEN_EXECUTION_KILL_BLOCK", ticket, type, volume, 0.0, open_price, 0.0, current_sl, new_sl, tp, trigger_r, result, "EXECUTION_KILL_SWITCH_BLOCK");
      return false;
   }
   request.action = TRADE_ACTION_SLTP;
   request.position = ticket;
   request.symbol = _Symbol;
   request.magic = InpMagicNumber;
   request.sl = new_sl;
   request.tp = tp;
   bool sent = OrderSend(request, result);
   WriteManagementRow(sent ? "BREAKEVEN_SLTP_SENT" : "BREAKEVEN_SLTP_FAIL", ticket, type, volume, 0.0, open_price, 0.0, current_sl, new_sl, tp, trigger_r, result, "BREAKEVEN_TRIGGER");
   return sent;
}

bool TakePartialProfit(const ulong ticket, const ENUM_POSITION_TYPE type, const double volume, const double open_price, const double current_sl, const double tp, const double trigger_r)
{
   string state_name = PositionActionStateName("A3BRK_PARTIAL", ticket);
   if(GlobalVariableCheck(state_name))
      return false;

   double min_volume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double requested_volume = NormalizePartialVolume(volume * InpPartialCloseFraction);
   MqlTradeResult result;
   ZeroMemory(result);
   if(ExecutionKillSwitchActive())
   {
      WriteManagementRow("PARTIAL_EXECUTION_KILL_BLOCK", ticket, type, volume, requested_volume, open_price, 0.0, current_sl, current_sl, tp, trigger_r, result, "EXECUTION_KILL_SWITCH_BLOCK");
      return false;
   }
   if(requested_volume < min_volume || volume - requested_volume < min_volume)
   {
      GlobalVariableSet(state_name, 1.0);
      WriteManagementRow("PARTIAL_SKIP_MIN_VOLUME", ticket, type, volume, requested_volume, open_price, 0.0, current_sl, current_sl, tp, trigger_r, result, "FIXED_001_LOT_CANNOT_LEAVE_RUNNER");
      return false;
   }

   MqlTradeRequest request;
   ZeroMemory(request);
   request.action = TRADE_ACTION_DEAL;
   request.position = ticket;
   request.symbol = _Symbol;
   request.magic = InpMagicNumber;
   request.volume = requested_volume;
   request.type = type == POSITION_TYPE_BUY ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
   request.price = type == POSITION_TYPE_BUY ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   request.deviation = InpDeviationPoints;
   request.type_filling = FillPolicy();
   request.type_time = ORDER_TIME_GTC;
   request.comment = InpOrderComment + "_PARTIAL";
   bool sent = OrderSend(request, result);
   if(sent && (result.retcode == TRADE_RETCODE_DONE || result.retcode == TRADE_RETCODE_DONE_PARTIAL))
      GlobalVariableSet(state_name, 1.0);
   WriteManagementRow(sent ? "PARTIAL_CLOSE_SENT" : "PARTIAL_CLOSE_FAIL", ticket, type, volume, requested_volume, open_price, request.price, current_sl, current_sl, tp, trigger_r, result, "PARTIAL_TRIGGER");
   return sent;
}

void ManageOpenPositions()
{
   if(!InpBreakevenEnabled && !InpPartialTakeProfitEnabled)
      return;
   for(int index = 0; index < PositionsTotal(); index++)
   {
      ulong ticket = PositionGetTicket(index);
      if(ticket == 0)
         continue;
      if(!PositionSelectByTicket(ticket))
         continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || (int)PositionGetInteger(POSITION_MAGIC) != InpMagicNumber)
         continue;
      ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      double volume = PositionGetDouble(POSITION_VOLUME);
      double open_price = PositionGetDouble(POSITION_PRICE_OPEN);
      double sl = PositionGetDouble(POSITION_SL);
      double tp = PositionGetDouble(POSITION_TP);
      double favorable_r = PositionFavorableR(type, open_price, sl);
      if(InpBreakevenEnabled && favorable_r >= InpBreakevenTriggerR)
         MoveStopToBreakeven(ticket, type, volume, open_price, sl, tp, favorable_r);
      if(InpPartialTakeProfitEnabled && favorable_r >= InpPartialTriggerR)
         TakePartialProfit(ticket, type, volume, open_price, sl, tp, favorable_r);
   }
}

int OnInit()
{
   if(!EnsureStartupLogHeader() || !EnsureSignalLogHeader() || !EnsureOrderLogHeader() || !EnsureManagementLogHeader())
      return INIT_FAILED;
   if(InpMagicNumber != A3_BREAKOUT_EXPECTED_MAGIC)
   {
      WriteStartupRow("SCOPE_LOCK_MAGIC_BLOCK");
      return INIT_FAILED;
   }
   string scope_reason = "";
   if(!ScopeLocksPass(scope_reason))
   {
      WriteStartupRow(scope_reason);
      return INIT_FAILED;
   }
   g_breakout_observer.Configure(false);
   WriteStartupRow(A3_BREAKOUT_ATTACHED_STATUS);
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   WriteStartupRow("REMOVED_REASON_" + IntegerToString(reason));
}

void OnTimer()
{
   ManageOpenPositions();

   datetime m5_bar_time = iTime(_Symbol, PERIOD_M5, 0);
   if(m5_bar_time <= 0 || m5_bar_time == g_last_m5_bar_time)
      return;
   g_last_m5_bar_time = m5_bar_time;

   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   Phase1BreakoutRetestObservation observation;
   Phase1ResetBreakoutRetestObservation(observation);
   g_breakout_observer.Evaluate(_Symbol, point, observation);
   ApplySoftRetestFilter(observation);

   double spread_points = CurrentSpreadPoints();
   double estimated_cost_r = EstimatedCostRForObservation(observation, spread_points);
   int h1_trend = TrendDirection(PERIOD_H1, InpTrendH1LookbackBars);
   int h4_trend = TrendDirection(PERIOD_H4, InpTrendH4LookbackBars);
   string guard_reason = observation.would_signal ? "PASS" : "NO_SIGNAL";
   string trend_reason = InpTrendGuardEnabled ? "TREND_NOT_CHECKED" : "TREND_GUARD_DISABLED";
   string trend_shadow_reason = InpTrendGuardShadowOnly ? "TREND_SHADOW_NOT_CHECKED" : "TREND_SHADOW_DISABLED";
   bool trend_shadow_pass = true;
   if(InpTrendGuardShadowOnly)
      trend_shadow_pass = TrendGuardDecision(observation, h1_trend, h4_trend, trend_shadow_reason);
   bool guard_pass = TradingGuardsPass(observation, spread_points, estimated_cost_r, h1_trend, h4_trend, guard_reason, trend_reason);
   WriteSignalRow(observation, spread_points, estimated_cost_r, guard_reason, guard_pass, h1_trend, h4_trend, trend_reason, trend_shadow_pass, trend_shadow_reason);
   if(guard_pass)
      SendMarketOrder(observation, spread_points, estimated_cost_r);
}

#endif
