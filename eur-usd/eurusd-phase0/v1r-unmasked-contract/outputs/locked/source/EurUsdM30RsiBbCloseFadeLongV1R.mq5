//+------------------------------------------------------------------+
//| EurUsdM30RsiBbCloseFadeLongV1R.mq5                                |
//| Source-bound, tester-only EURUSD V1R contract-repair baseline.    |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - EURUSD research lane"
#property version   "1.100"
#property strict

#include <Trade/Trade.mqh>

enum MeanReversionSignalMode
  {
   MR_BB_CLOSE_FADE = 0,
   MR_BB_WICK_RECLAIM = 1,
   MR_RSI_EXTREME_FADE = 2
  };

enum DirectionMode
  {
   DIR_BOTH = 0,
   DIR_LONG_ONLY = 1,
   DIR_SHORT_ONLY = 2
  };

input string                  InpRunId                   = "EURUSD_M30_RSI_BB_CLOSE_FADE_LONG_V1R_UNMASKED_CONTRACT";
input string                  InpTargetSymbol            = "EURUSD";
input ENUM_TIMEFRAMES         InpSignalTimeframe         = PERIOD_M30;
input long                    InpMagicNumber             = 26723003;
input MeanReversionSignalMode InpSignalMode              = MR_BB_CLOSE_FADE;
input DirectionMode           InpDirectionMode           = DIR_LONG_ONLY;
input double                  InpFixedLots               = 0.01;
input int                     InpDeviationPoints         = 30;
input int                     InpMaxSpreadPoints         = 100;
input int                     InpMaxTradesPerDay         = 20;
input int                     InpCooldownMinutes         = 0;
input string                  InpBlockedEntryHoursCsv    = "";
input int                     InpAtrPeriod               = 14;
input int                     InpBandsPeriod             = 20;
input double                  InpBandsDeviation          = 2.0;
input int                     InpRsiPeriod               = 14;
input bool                    InpUseRsiFilter            = true;
input double                  InpRsiOversold             = 35.0;
input double                  InpRsiOverbought           = 65.0;
input double                  InpMinBandDistanceAtr      = 0.00;
input double                  InpMinBodyFraction         = 0.40;
input double                  InpStopAtrMultiple         = 1.40;
input int                     InpStopFloorPoints         = 30;
input int                     InpStopCeilingPoints       = 700;
input double                  InpRiskReward              = 0.80;
input string                  InpStartupLogFileName      = "eurusd_v1r_startup_log.csv";
input string                  InpSignalLogFileName       = "eurusd_v1r_signal_log.csv";
input string                  InpOrderLogFileName        = "eurusd_v1r_order_log.csv";
input string                  InpStateLogFileName        = "eurusd_v1r_state_log.csv";
input string                  InpEnvironmentLogFileName  = "eurusd_v1r_environment_log.csv";
input string                  InpExecutionLogFileName    = "eurusd_v1r_execution_log.csv";
input string                  InpTransactionLogFileName  = "eurusd_v1r_transaction_log.csv";
input string                  InpManagementLogFileName   = "eurusd_v1r_management_log.csv";
input string                  InpOrderComment            = "EU_M30_V1R";

CTrade   g_trade;
int      g_atr_handle = INVALID_HANDLE;
int      g_bands_handle = INVALID_HANDLE;
int      g_rsi_handle = INVALID_HANDLE;
datetime g_last_signal_bar = 0;
datetime g_last_trade_time = 0;
string   g_trade_day = "";
int      g_trades_today = 0;
bool     g_skip_first_observed_transition = true;

string Timestamp()
  {
   return TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
  }

string TimestampValue(const datetime value)
  {
   if(value <= 0)
      return "";
   return TimeToString(value, TIME_DATE | TIME_SECONDS);
  }

string BoolText(const bool value) { return value ? "true" : "false"; }

string CsvEscape(string value)
  {
   StringReplace(value, "\"", "\"\"");
   if(StringFind(value, ",") >= 0 || StringFind(value, "\"") >= 0 || StringFind(value, "\n") >= 0 || StringFind(value, "\r") >= 0)
      return "\"" + value + "\"";
   return value;
  }

string JoinCsv(const string &values[])
  {
   string row = "";
   for(int i = 0; i < ArraySize(values); i++)
     {
      if(i > 0)
         row += ",";
      row += CsvEscape(values[i]);
     }
   return row;
  }

void EnsureCsvHeader(const string file_name, const string header)
  {
   if(FileIsExist(file_name))
      return;
   const int handle = FileOpen(file_name, FILE_WRITE | FILE_TXT | FILE_ANSI);
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("EURUSD_V1R: failed to create log %s err=%d", file_name, GetLastError());
      return;
     }
   FileWriteString(handle, header + "\r\n");
   FileClose(handle);
  }

void AppendCsvLine(const string file_name, const string header, const string &values[])
  {
   const bool exists = FileIsExist(file_name);
   const int handle = FileOpen(file_name, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI);
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("EURUSD_V1R: failed to open log %s err=%d", file_name, GetLastError());
      return;
     }
   FileSeek(handle, 0, SEEK_END);
   if(!exists)
      FileWriteString(handle, header + "\r\n");
   FileWriteString(handle, JoinCsv(values) + "\r\n");
   FileClose(handle);
  }

void LogStartup(const string status, const string detail)
  {
   string values[];
   ArrayResize(values, 14);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = AccountInfoString(ACCOUNT_SERVER);
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = BoolText((bool)MQLInfoInteger(MQL_TESTER));
   values[7] = IntegerToString((int)InpSignalMode);
   values[8] = IntegerToString((int)InpDirectionMode);
   values[9] = DoubleToString(InpRiskReward, 2);
   values[10] = TimestampValue(g_last_signal_bar);
   values[11] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LEVERAGE));
   values[12] = status;
   values[13] = detail;
   AppendCsvLine(
      InpStartupLogFileName,
      "timestamp_broker,run_id,server,account,symbol,magic,is_tester,signal_mode,direction_mode,risk_reward,latch_bar_open,account_leverage,status,detail",
      values
   );
  }

void LogEnvironmentValue(const string key, const string value)
  {
   string values[];
   ArrayResize(values, 5);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = InpTargetSymbol;
   values[3] = key;
   values[4] = value;
   AppendCsvLine(
      InpEnvironmentLogFileName,
      "timestamp_broker,run_id,symbol,key,value",
      values
   );
  }

void LogEnvironment()
  {
   LogEnvironmentValue("account_server", AccountInfoString(ACCOUNT_SERVER));
   LogEnvironmentValue("account_currency", AccountInfoString(ACCOUNT_CURRENCY));
   LogEnvironmentValue("account_leverage", IntegerToString((int)AccountInfoInteger(ACCOUNT_LEVERAGE)));
   LogEnvironmentValue("account_margin_mode", IntegerToString((int)AccountInfoInteger(ACCOUNT_MARGIN_MODE)));
   LogEnvironmentValue("terminal_build", IntegerToString((int)TerminalInfoInteger(TERMINAL_BUILD)));
   LogEnvironmentValue("mql_program_path", MQLInfoString(MQL_PROGRAM_PATH));
   LogEnvironmentValue("tester_model_annotation", "Model=0 may contain generated ticks; native-real-tick coverage not established");
   LogEnvironmentValue("server_time", TimestampValue(TimeTradeServer()));
   LogEnvironmentValue("gmt_time", TimestampValue(TimeGMT()));
   LogEnvironmentValue("gmt_offset_seconds", IntegerToString(TimeGMTOffset()));
   LogEnvironmentValue("daylight_savings_seconds", IntegerToString(TimeDaylightSavings()));
   LogEnvironmentValue("symbol_digits", IntegerToString((int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_DIGITS)));
   LogEnvironmentValue("symbol_point", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_POINT), 10));
   LogEnvironmentValue("contract_size", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_CONTRACT_SIZE), 8));
   LogEnvironmentValue("tick_size", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_SIZE), 10));
   LogEnvironmentValue("tick_value_profit", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_VALUE_PROFIT), 8));
   LogEnvironmentValue("tick_value_loss", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_TRADE_TICK_VALUE_LOSS), 8));
   LogEnvironmentValue("volume_min", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN), 8));
   LogEnvironmentValue("volume_max", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MAX), 8));
   LogEnvironmentValue("volume_step", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP), 8));
   LogEnvironmentValue("stops_level_points", IntegerToString((int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_TRADE_STOPS_LEVEL)));
   LogEnvironmentValue("freeze_level_points", IntegerToString((int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_TRADE_FREEZE_LEVEL)));
   LogEnvironmentValue("spread_float", BoolText((bool)SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD_FLOAT)));
   LogEnvironmentValue("trade_mode", IntegerToString((int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_TRADE_MODE)));
   LogEnvironmentValue("margin_calc_mode", IntegerToString((int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_TRADE_CALC_MODE)));
   LogEnvironmentValue("swap_mode", IntegerToString((int)SymbolInfoInteger(InpTargetSymbol, SYMBOL_SWAP_MODE)));
   LogEnvironmentValue("swap_long", DoubleToString(SymbolInfoDouble(InpTargetSymbol, SYMBOL_SWAP_LONG), 8));
   LogEnvironmentValue("currency_base", SymbolInfoString(InpTargetSymbol, SYMBOL_CURRENCY_BASE));
   LogEnvironmentValue("currency_profit", SymbolInfoString(InpTargetSymbol, SYMBOL_CURRENCY_PROFIT));
   LogEnvironmentValue("currency_margin", SymbolInfoString(InpTargetSymbol, SYMBOL_CURRENCY_MARGIN));
  }

void LogState(const string event_name, const datetime current_bar_open, const datetime processed_bar_open, const string detail)
  {
   string values[];
   ArrayResize(values, 7);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = InpTargetSymbol;
   values[3] = event_name;
   values[4] = TimestampValue(current_bar_open);
   values[5] = TimestampValue(processed_bar_open);
   values[6] = detail;
   AppendCsvLine(
      InpStateLogFileName,
      "decision_tick_broker,run_id,symbol,event,current_bar_open,processed_bar_open,detail",
      values
   );
  }

void LogSignal(
   const string direction,
   const string reason,
   const double open_price,
   const double high_price,
   const double low_price,
   const double close_price,
   const double atr,
   const double band_upper,
   const double band_mid,
   const double band_lower,
   const double rsi,
   const double body_fraction,
   const double band_distance_atr,
   const long spread_points
)
  {
   string values[];
   ArrayResize(values, 23);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[3] = _Symbol;
   values[4] = direction;
   values[5] = reason;
   values[6] = DoubleToString(open_price, _Digits);
   values[7] = DoubleToString(high_price, _Digits);
   values[8] = DoubleToString(low_price, _Digits);
   values[9] = DoubleToString(close_price, _Digits);
   values[10] = DoubleToString(atr, _Digits);
   values[11] = DoubleToString(band_upper, _Digits);
   values[12] = DoubleToString(band_mid, _Digits);
   values[13] = DoubleToString(band_lower, _Digits);
   values[14] = DoubleToString(rsi, 2);
   values[15] = DoubleToString(body_fraction, 4);
   values[16] = DoubleToString(band_distance_atr, 4);
   values[17] = IntegerToString((int)spread_points);
   values[18] = IntegerToString((int)InpSignalMode);
   values[19] = "";
   values[20] = TimestampValue(iTime(InpTargetSymbol, InpSignalTimeframe, 1));
   values[21] = TimestampValue(iTime(InpTargetSymbol, InpSignalTimeframe, 0));
   values[22] = Timestamp();
   AppendCsvLine(
      InpSignalLogFileName,
      "timestamp_broker,run_id,account,symbol,direction,reason,open,high,low,close,atr,band_upper,band_mid,band_lower,rsi,body_fraction,band_distance_atr,spread_points,signal_mode,extra,setup_bar_open,setup_bar_close,decision_tick_broker",
      values
   );
  }

void LogOrder(
   const string action,
   const string direction,
   const string reason,
   const double lots,
   const double bid,
   const double ask,
   const long spread_points,
   const double sl,
   const double tp,
   const double stop_points,
   const long retcode,
   const string retcode_description,
   const ulong order_ticket,
   const ulong deal_ticket,
   const double result_price
)
  {
   string values[];
   ArrayResize(values, 20);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[3] = _Symbol;
   values[4] = IntegerToString((int)InpMagicNumber);
   values[5] = action;
   values[6] = direction;
   values[7] = DoubleToString(lots, 2);
   values[8] = DoubleToString(bid, _Digits);
   values[9] = DoubleToString(ask, _Digits);
   values[10] = IntegerToString((int)spread_points);
   values[11] = DoubleToString(sl, _Digits);
   values[12] = DoubleToString(tp, _Digits);
   values[13] = DoubleToString(stop_points, 2);
   values[14] = IntegerToString((int)retcode);
   values[15] = retcode_description;
   values[16] = IntegerToString((int)order_ticket);
   values[17] = IntegerToString((int)deal_ticket) + "|result_price=" + DoubleToString(result_price, _Digits) + "|reason=" + reason;
   values[18] = TimestampValue(iTime(InpTargetSymbol, InpSignalTimeframe, 1));
   values[19] = Timestamp();
   AppendCsvLine(
      InpOrderLogFileName,
      "timestamp_broker,run_id,account,symbol,magic,action,direction,lots,bid,ask,spread_points,sl,tp,stop_points,retcode,retcode_description,order_ticket,deal_and_reason,setup_bar_open,decision_tick_broker",
      values
   );
  }

void LogExecution(
   const string event_name,
   const string direction,
   const string reason,
   const double bid,
   const double ask,
   const long symbol_spread_points,
   const double quoted_spread_points,
   const double atr,
   const double recent_low,
   const double recent_high,
   const double atr_component_points,
   const double floor_component_points,
   const double swing_component_points,
   const string selected_stop_component,
   const double requested_sl,
   const double requested_tp,
   const double stop_points,
   const bool request_ok,
   const bool fill_confirmed,
   const long retcode,
   const ulong order_ticket,
   const ulong deal_ticket,
   const double result_price,
   const double actual_position_price,
   const double actual_sl,
   const double actual_tp
)
  {
   string values[];
   ArrayResize(values, 34);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = InpTargetSymbol;
   values[3] = event_name;
   values[4] = direction;
   values[5] = reason;
   values[6] = TimestampValue(iTime(InpTargetSymbol, InpSignalTimeframe, 1));
   values[7] = Timestamp();
   values[8] = DoubleToString(bid, _Digits);
   values[9] = DoubleToString(ask, _Digits);
   values[10] = IntegerToString((int)symbol_spread_points);
   values[11] = DoubleToString(quoted_spread_points, 2);
   values[12] = DoubleToString(atr, _Digits);
   values[13] = DoubleToString(recent_low, _Digits);
   values[14] = DoubleToString(recent_high, _Digits);
   values[15] = DoubleToString(atr_component_points, 2);
   values[16] = DoubleToString(floor_component_points, 2);
   values[17] = DoubleToString(swing_component_points, 2);
   values[18] = selected_stop_component;
   values[19] = DoubleToString(requested_sl, _Digits);
   values[20] = DoubleToString(requested_tp, _Digits);
   values[21] = DoubleToString(stop_points, 2);
   values[22] = BoolText(request_ok);
   values[23] = BoolText(fill_confirmed);
   values[24] = IntegerToString((int)retcode);
   values[25] = IntegerToString((int)order_ticket);
   values[26] = IntegerToString((int)deal_ticket);
   values[27] = DoubleToString(result_price, _Digits);
   values[28] = DoubleToString(actual_position_price, _Digits);
   values[29] = DoubleToString(actual_sl, _Digits);
   values[30] = DoubleToString(actual_tp, _Digits);
   values[31] = DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2);
   values[32] = DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 4);
   values[33] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LEVERAGE));
   AppendCsvLine(
      InpExecutionLogFileName,
      "timestamp_broker,run_id,symbol,event,direction,reason,setup_bar_open,decision_tick_broker,bid,ask,symbol_spread_points,quoted_spread_points,atr,recent_low,recent_high,atr_component_points,floor_component_points,swing_component_points,selected_stop_component,requested_sl,requested_tp,stop_points,request_ok,fill_confirmed,retcode,order_ticket,deal_ticket,result_price,actual_position_price,actual_sl,actual_tp,free_margin,margin_level,account_leverage",
      values
   );
  }

bool CopyOne(const int handle, const int buffer_index, const int shift, double &value)
  {
   double buffer[];
   ArrayResize(buffer, 1);
   if(CopyBuffer(handle, buffer_index, shift, 1, buffer) != 1)
      return false;
   value = buffer[0];
   return value != EMPTY_VALUE;
  }

double RecentHigh(const int start_shift, const int count)
  {
   double value = 0.0;
   for(int shift = start_shift; shift < start_shift + count; shift++)
     {
      const double high = iHigh(InpTargetSymbol, InpSignalTimeframe, shift);
      if(high <= 0.0)
         continue;
      if(value == 0.0 || high > value)
         value = high;
     }
   return value;
  }

double RecentLow(const int start_shift, const int count)
  {
   double value = 0.0;
   for(int shift = start_shift; shift < start_shift + count; shift++)
     {
      const double low = iLow(InpTargetSymbol, InpSignalTimeframe, shift);
      if(low <= 0.0)
         continue;
      if(value == 0.0 || low < value)
         value = low;
     }
   return value;
  }

bool DirectionModeAllows(const string direction)
  {
   if(InpDirectionMode == DIR_BOTH)
      return true;
   if(InpDirectionMode == DIR_LONG_ONLY && direction == "LONG")
      return true;
   if(InpDirectionMode == DIR_SHORT_ONLY && direction == "SHORT")
      return true;
   return false;
  }

bool EntryHourBlocked()
  {
   if(InpBlockedEntryHoursCsv == "")
      return false;
   MqlDateTime parts;
   TimeToStruct(TimeCurrent(), parts);
   string token = "";
   for(int i = 0; i <= StringLen(InpBlockedEntryHoursCsv); i++)
     {
      const ushort ch = (i < StringLen(InpBlockedEntryHoursCsv)) ? StringGetCharacter(InpBlockedEntryHoursCsv, i) : ',';
      if(ch == ',')
        {
         StringTrimLeft(token);
         StringTrimRight(token);
         if(token != "" && (int)StringToInteger(token) == parts.hour)
            return true;
         token = "";
        }
      else
         token += ShortToString(ch);
     }
   return false;
  }

int CountOwnOpenPositions()
  {
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetInteger(POSITION_MAGIC) == InpMagicNumber && PositionGetString(POSITION_SYMBOL) == InpTargetSymbol)
         count++;
     }
   return count;
  }

void UpdateTradeDay()
  {
   MqlDateTime parts;
   TimeToStruct(TimeCurrent(), parts);
   const string day = IntegerToString(parts.year) + "." + IntegerToString(parts.mon) + "." + IntegerToString(parts.day);
   if(day != g_trade_day)
     {
      g_trade_day = day;
      g_trades_today = 0;
     }
  }

double NormalizeVolume(const double lots)
  {
   const double min_lots = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN);
   const double max_lots = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MAX);
   const double step = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
   if(min_lots <= 0.0 || max_lots <= 0.0 || step <= 0.0)
      return 0.0;
   double normalized = MathFloor(lots / step + 0.0000001) * step;
   if(normalized < min_lots)
      normalized = min_lots;
   if(normalized > max_lots)
      normalized = max_lots;
   return NormalizeDouble(normalized, 2);
  }

bool BuildSignal(
   string &direction,
   string &reason,
   double &band_distance_atr,
   const double open_price,
   const double high_price,
   const double low_price,
   const double close_price,
   const double atr,
   const double band_upper,
   const double band_mid,
   const double band_lower,
   const double rsi,
   const double body_fraction
)
  {
   direction = "";
   reason = "";
   band_distance_atr = 0.0;
   const bool rsi_long_ok = !InpUseRsiFilter || rsi <= InpRsiOversold;
   const bool rsi_short_ok = !InpUseRsiFilter || rsi >= InpRsiOverbought;

   if(InpSignalMode == MR_BB_CLOSE_FADE)
     {
      const double lower_distance = atr > 0.0 ? (band_lower - close_price) / atr : 0.0;
      const double upper_distance = atr > 0.0 ? (close_price - band_upper) / atr : 0.0;
      if(close_price <= band_lower && rsi_long_ok && lower_distance >= InpMinBandDistanceAtr)
        {
         direction = "LONG";
         reason = "M5_BB_CLOSE_FADE_LONG";
         band_distance_atr = lower_distance;
        }
      else if(close_price >= band_upper && rsi_short_ok && upper_distance >= InpMinBandDistanceAtr)
        {
         direction = "SHORT";
         reason = "M5_BB_CLOSE_FADE_SHORT";
         band_distance_atr = upper_distance;
        }
     }
   else if(InpSignalMode == MR_BB_WICK_RECLAIM)
     {
      const double lower_distance = atr > 0.0 ? (band_lower - low_price) / atr : 0.0;
      const double upper_distance = atr > 0.0 ? (high_price - band_upper) / atr : 0.0;
      if(low_price <= band_lower && close_price > band_lower && close_price > open_price && rsi_long_ok && lower_distance >= InpMinBandDistanceAtr)
        {
         direction = "LONG";
         reason = "M5_BB_WICK_RECLAIM_LONG";
         band_distance_atr = lower_distance;
        }
      else if(high_price >= band_upper && close_price < band_upper && close_price < open_price && rsi_short_ok && upper_distance >= InpMinBandDistanceAtr)
        {
         direction = "SHORT";
         reason = "M5_BB_WICK_RECLAIM_SHORT";
         band_distance_atr = upper_distance;
        }
     }
   else if(InpSignalMode == MR_RSI_EXTREME_FADE)
     {
      if(rsi <= InpRsiOversold && close_price < band_mid)
        {
         direction = "LONG";
         reason = "M5_RSI_EXTREME_FADE_LONG";
         band_distance_atr = atr > 0.0 ? (band_mid - close_price) / atr : 0.0;
        }
      else if(rsi >= InpRsiOverbought && close_price > band_mid)
        {
         direction = "SHORT";
         reason = "M5_RSI_EXTREME_FADE_SHORT";
         band_distance_atr = atr > 0.0 ? (close_price - band_mid) / atr : 0.0;
        }
     }

   if(direction == "")
      return false;
   if(InpMinBodyFraction > 0.0 && body_fraction < InpMinBodyFraction)
      return false;
   return true;
  }

void LogSimpleExecution(
   const string event_name,
   const string direction,
   const string reason,
   const double bid,
   const double ask,
   const long spread_points,
   const double atr
)
  {
   const double quoted_spread_points = _Point > 0.0 ? (ask - bid) / _Point : 0.0;
   LogExecution(event_name, direction, reason, bid, ask, spread_points, quoted_spread_points, atr, 0.0, 0.0, 0.0, (double)InpStopFloorPoints, 0.0, "", 0.0, 0.0, 0.0, false, false, 0, 0, 0, 0.0, 0.0, 0.0, 0.0);
  }

void EvaluateCompletedSignalBar()
  {
   UpdateTradeDay();
   if(iBars(InpTargetSymbol, InpSignalTimeframe) < 100)
      return;

   double atr = 0.0;
   double band_mid = 0.0;
   double band_upper = 0.0;
   double band_lower = 0.0;
   double rsi = 0.0;
   if(!CopyOne(g_atr_handle, 0, 1, atr))
      return;
   if(!CopyOne(g_bands_handle, 0, 1, band_mid) || !CopyOne(g_bands_handle, 1, 1, band_upper) || !CopyOne(g_bands_handle, 2, 1, band_lower))
      return;
   if(!CopyOne(g_rsi_handle, 0, 1, rsi))
      return;
   if(atr <= 0.0 || band_upper <= band_lower)
      return;

   const double open_price = iOpen(InpTargetSymbol, InpSignalTimeframe, 1);
   const double high_price = iHigh(InpTargetSymbol, InpSignalTimeframe, 1);
   const double low_price = iLow(InpTargetSymbol, InpSignalTimeframe, 1);
   const double close_price = iClose(InpTargetSymbol, InpSignalTimeframe, 1);
   const double range = MathMax(high_price - low_price, _Point);
   const double body_fraction = MathAbs(close_price - open_price) / range;
   string direction = "";
   string reason = "";
   double band_distance_atr = 0.0;
   if(!BuildSignal(direction, reason, band_distance_atr, open_price, high_price, low_price, close_price, atr, band_upper, band_mid, band_lower, rsi, body_fraction))
      return;

   const long spread_points = SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD);
   LogSignal(direction, reason, open_price, high_price, low_price, close_price, atr, band_upper, band_mid, band_lower, rsi, body_fraction, band_distance_atr, spread_points);

   const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
   const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
   LogSimpleExecution("DECISION_QUOTE", direction, "raw_setup", bid, ask, spread_points, atr);
   if(!DirectionModeAllows(direction))
     {
      LogOrder("GUARD_BLOCK", direction, "direction_mode_block", 0.0, bid, ask, spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(EntryHourBlocked())
     {
      LogOrder("GUARD_BLOCK", direction, "blocked_entry_hour", 0.0, bid, ask, spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(CountOwnOpenPositions() > 0)
     {
      LogOrder("GUARD_BLOCK", direction, "own_position_exists", 0.0, bid, ask, spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(InpMaxTradesPerDay > 0 && g_trades_today >= InpMaxTradesPerDay)
     {
      LogOrder("GUARD_BLOCK", direction, "daily_trade_cap", 0.0, bid, ask, spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(g_last_trade_time > 0 && InpCooldownMinutes > 0 && TimeCurrent() - g_last_trade_time < InpCooldownMinutes * 60)
     {
      LogOrder("GUARD_BLOCK", direction, "cooldown_active", 0.0, bid, ask, spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(spread_points > InpMaxSpreadPoints)
     {
      LogOrder("GUARD_BLOCK", direction, "spread_too_high", 0.0, bid, ask, spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
     {
      LogOrder("GUARD_BLOCK", direction, "terminal_or_account_trading_disabled", 0.0, bid, ask, spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }

   const double recent_low = RecentLow(1, 6);
   const double recent_high = RecentHigh(1, 6);
   const double atr_component_points = InpStopAtrMultiple * atr / _Point;
   const double floor_component_points = (double)InpStopFloorPoints;
   double stop_distance = MathMax(InpStopAtrMultiple * atr, InpStopFloorPoints * _Point);
   double sl = 0.0;
   double tp = 0.0;
   double stop_points = 0.0;
   double swing_component_points = 0.0;
   string selected_stop_component = atr_component_points >= floor_component_points ? "ATR" : "FLOOR";
   if(direction == "LONG")
     {
      swing_component_points = recent_low > 0.0 ? (ask - recent_low) / _Point : 0.0;
      sl = NormalizeDouble(MathMin(recent_low, ask - stop_distance), _Digits);
      stop_distance = ask - sl;
      stop_points = stop_distance / _Point;
      tp = NormalizeDouble(ask + InpRiskReward * stop_distance, _Digits);
      if(swing_component_points > MathMax(atr_component_points, floor_component_points))
         selected_stop_component = "SWING_LOW";
     }
   else
     {
      swing_component_points = recent_high > 0.0 ? (recent_high - bid) / _Point : 0.0;
      sl = NormalizeDouble(MathMax(recent_high, bid + stop_distance), _Digits);
      stop_distance = sl - bid;
      stop_points = stop_distance / _Point;
      tp = NormalizeDouble(bid - InpRiskReward * stop_distance, _Digits);
      if(swing_component_points > MathMax(atr_component_points, floor_component_points))
         selected_stop_component = "SWING_HIGH";
     }

   const double quoted_spread_points = _Point > 0.0 ? (ask - bid) / _Point : 0.0;
   LogExecution("STOP_GEOMETRY", direction, "geometry_ready", bid, ask, spread_points, quoted_spread_points, atr, recent_low, recent_high, atr_component_points, floor_component_points, swing_component_points, selected_stop_component, sl, tp, stop_points, false, false, 0, 0, 0, 0.0, 0.0, 0.0, 0.0);
   if(InpStopCeilingPoints > 0 && stop_points > InpStopCeilingPoints)
     {
      LogOrder("GUARD_BLOCK", direction, "stop_ceiling_exceeded", 0.0, bid, ask, spread_points, sl, tp, stop_points, 0, "", 0, 0, 0.0);
      return;
     }
   const double lots = NormalizeVolume(InpFixedLots);
   if(lots <= 0.0)
     {
      LogOrder("GUARD_BLOCK", direction, "invalid_lots", 0.0, bid, ask, spread_points, sl, tp, stop_points, 0, "", 0, 0, 0.0);
      return;
     }

   bool request_ok = false;
   if(direction == "LONG")
      request_ok = g_trade.Buy(lots, InpTargetSymbol, 0.0, sl, tp, InpOrderComment);
   else
      request_ok = g_trade.Sell(lots, InpTargetSymbol, 0.0, sl, tp, InpOrderComment);

   const ulong result_deal = g_trade.ResultDeal();
   const long result_retcode = (long)g_trade.ResultRetcode();
   const bool fill_confirmed = request_ok && result_deal > 0 &&
      (result_retcode == TRADE_RETCODE_DONE || result_retcode == TRADE_RETCODE_DONE_PARTIAL);
   const string action = fill_confirmed ? "ORDER_SEND_OK" : "ORDER_SEND_FAIL";
   string result_reason = "order_send_failed";
   if(fill_confirmed)
      result_reason = "entered";
   else if(request_ok)
      result_reason = "request_accepted_no_entry_deal";
   LogOrder(action, direction, result_reason, lots, bid, ask, spread_points, sl, tp, stop_points, result_retcode, g_trade.ResultRetcodeDescription(), g_trade.ResultOrder(), result_deal, g_trade.ResultPrice());

   double actual_position_price = 0.0;
   double actual_sl = 0.0;
   double actual_tp = 0.0;
   if(fill_confirmed && PositionSelect(InpTargetSymbol) && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
     {
      actual_position_price = PositionGetDouble(POSITION_PRICE_OPEN);
      actual_sl = PositionGetDouble(POSITION_SL);
      actual_tp = PositionGetDouble(POSITION_TP);
     }
   LogExecution("REQUEST_RESULT", direction, result_reason, bid, ask, spread_points, quoted_spread_points, atr, recent_low, recent_high, atr_component_points, floor_component_points, swing_component_points, selected_stop_component, sl, tp, stop_points, request_ok, fill_confirmed, result_retcode, g_trade.ResultOrder(), result_deal, g_trade.ResultPrice(), actual_position_price, actual_sl, actual_tp);
   if(fill_confirmed)
     {
      g_trades_today++;
      g_last_trade_time = TimeCurrent();
     }
  }

int OnInit()
  {
   if(!MQLInfoInteger(MQL_TESTER))
     {
      LogStartup("INIT_FAILED_NOT_TESTER", "Strategy Tester only.");
      return INIT_FAILED;
     }
   if(_Symbol != InpTargetSymbol)
     {
      LogStartup("INIT_FAILED_WRONG_SYMBOL", _Symbol + " != " + InpTargetSymbol);
      return INIT_FAILED;
     }
   if(!SymbolSelect(InpTargetSymbol, true))
     {
      LogStartup("INIT_FAILED_SYMBOL_SELECT", InpTargetSymbol);
      return INIT_FAILED;
     }
   g_atr_handle = iATR(InpTargetSymbol, InpSignalTimeframe, InpAtrPeriod);
   g_bands_handle = iBands(InpTargetSymbol, InpSignalTimeframe, InpBandsPeriod, 0, InpBandsDeviation, PRICE_CLOSE);
   g_rsi_handle = iRSI(InpTargetSymbol, InpSignalTimeframe, InpRsiPeriod, PRICE_CLOSE);
   if(g_atr_handle == INVALID_HANDLE || g_bands_handle == INVALID_HANDLE || g_rsi_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_INDICATOR_HANDLE", "atr_bands_or_rsi_invalid");
      return INIT_FAILED;
     }

   g_last_signal_bar = iTime(InpTargetSymbol, InpSignalTimeframe, 0);
   g_skip_first_observed_transition = true;
   if(g_last_signal_bar <= 0)
     {
      LogStartup("INIT_FAILED_SIGNAL_BAR_TIME", "native signal bar unavailable");
      return INIT_FAILED;
     }

   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   EnsureCsvHeader(InpManagementLogFileName, "timestamp_broker,run_id,symbol,event,detail");
   EnsureCsvHeader(InpTransactionLogFileName, "timestamp_broker,run_id,symbol,transaction_type,order_ticket,deal_ticket,position_ticket,order_type,order_state,deal_type,deal_entry,volume,price,price_sl,price_tp,request_action,request_magic,request_volume,request_price,request_sl,request_tp,result_retcode,result_order,result_deal,result_price,result_bid,result_ask,result_comment");
   LogEnvironment();
   LogState("INIT_LATCH_ARMED", g_last_signal_bar, 0, "fail_closed_until_next_native_transition");
   LogStartup("INIT_OK_LATCH_ARMED", "tester_only; previous completed bar not evaluated");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   LogState("DEINIT", g_last_signal_bar, 0, IntegerToString(reason));
   if(g_atr_handle != INVALID_HANDLE)
      IndicatorRelease(g_atr_handle);
   if(g_bands_handle != INVALID_HANDLE)
      IndicatorRelease(g_bands_handle);
   if(g_rsi_handle != INVALID_HANDLE)
      IndicatorRelease(g_rsi_handle);
  }

void OnTick()
  {
   const datetime current_signal_bar = iTime(InpTargetSymbol, InpSignalTimeframe, 0);
   if(current_signal_bar == 0 || current_signal_bar == g_last_signal_bar)
      return;
   const datetime completed_signal_bar = g_last_signal_bar;
   g_last_signal_bar = current_signal_bar;
   if(g_skip_first_observed_transition)
     {
      g_skip_first_observed_transition = false;
      LogState("STARTUP_TRANSITION_SKIPPED", current_signal_bar, completed_signal_bar, "fail_closed_no_preinitialization_bar_evaluation");
      return;
     }
   LogState("NATIVE_BAR_TRANSITION", current_signal_bar, completed_signal_bar, "evaluate_completed_shift_1");
   EvaluateCompletedSignalBar();
  }

void OnTradeTransaction(
   const MqlTradeTransaction &trans,
   const MqlTradeRequest &request,
   const MqlTradeResult &result
)
  {
   long deal_entry = -1;
   if(trans.deal > 0 && HistoryDealSelect(trans.deal))
      deal_entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   string values[];
   ArrayResize(values, 28);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = trans.symbol;
   values[3] = IntegerToString((int)trans.type);
   values[4] = IntegerToString((int)trans.order);
   values[5] = IntegerToString((int)trans.deal);
   values[6] = IntegerToString((int)trans.position);
   values[7] = IntegerToString((int)trans.order_type);
   values[8] = IntegerToString((int)trans.order_state);
   values[9] = IntegerToString((int)trans.deal_type);
   values[10] = IntegerToString((int)deal_entry);
   values[11] = DoubleToString(trans.volume, 2);
   values[12] = DoubleToString(trans.price, _Digits);
   values[13] = DoubleToString(trans.price_sl, _Digits);
   values[14] = DoubleToString(trans.price_tp, _Digits);
   values[15] = IntegerToString((int)request.action);
   values[16] = IntegerToString((int)request.magic);
   values[17] = DoubleToString(request.volume, 2);
   values[18] = DoubleToString(request.price, _Digits);
   values[19] = DoubleToString(request.sl, _Digits);
   values[20] = DoubleToString(request.tp, _Digits);
   values[21] = IntegerToString((int)result.retcode);
   values[22] = IntegerToString((int)result.order);
   values[23] = IntegerToString((int)result.deal);
   values[24] = DoubleToString(result.price, _Digits);
   values[25] = DoubleToString(result.bid, _Digits);
   values[26] = DoubleToString(result.ask, _Digits);
   values[27] = result.comment;
   AppendCsvLine(
      InpTransactionLogFileName,
      "timestamp_broker,run_id,symbol,transaction_type,order_ticket,deal_ticket,position_ticket,order_type,order_state,deal_type,deal_entry,volume,price,price_sl,price_tp,request_action,request_magic,request_volume,request_price,request_sl,request_tp,result_retcode,result_order,result_deal,result_price,result_bid,result_ask,result_comment",
      values
   );
  }
