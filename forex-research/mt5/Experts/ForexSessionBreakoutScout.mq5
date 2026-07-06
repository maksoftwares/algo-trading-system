//+------------------------------------------------------------------+
//| ForexSessionBreakoutScout.mq5                                    |
//| Tester-only session range breakout scout for Forex research.      |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - forex research lane"
#property version   "1.000"
#property strict

#include <Trade/Trade.mqh>

enum DirectionMode
  {
   DIR_BOTH = 0,
   DIR_LONG_ONLY = 1,
   DIR_SHORT_ONLY = 2
  };

input string          InpRunId                   = "FOREX_SESSION_BREAKOUT_SCOUT";
input string          InpTargetSymbol            = "EURUSD";
input ENUM_TIMEFRAMES InpSignalTimeframe         = PERIOD_M5;
input long            InpMagicNumber             = 26070651;
input DirectionMode   InpDirectionMode           = DIR_BOTH;
input double          InpFixedLots               = 0.01;
input int             InpDeviationPoints         = 30;
input int             InpMaxSpreadPoints         = 100;
input int             InpMaxTradesPerDay         = 2;
input int             InpCooldownMinutes         = 0;
input string          InpBlockedEntryHoursCsv    = "";
input int             InpAtrPeriod               = 14;
input int             InpRangeStartHour          = 6;
input int             InpRangeStartMinute        = 0;
input int             InpRangeMinutes            = 60;
input int             InpTradeStartHour          = -1;
input int             InpTradeStartMinute        = 0;
input int             InpTradeWindowMinutes      = 240;
input double          InpBreakoutBufferAtr       = 0.05;
input double          InpMinRangeAtr             = 0.35;
input double          InpMaxRangeAtr             = 3.00;
input double          InpMinDailyRangeAtrFraction = 0.00;
input double          InpMinBodyFraction         = 0.30;
input double          InpLongCloseLocation       = 0.65;
input double          InpShortCloseLocation      = 0.35;
input double          InpStopAtrMultiple         = 1.00;
input double          InpStopRangeMultiple       = 1.00;
input int             InpStopFloorPoints         = 30;
input int             InpStopCeilingPoints       = 700;
input double          InpRiskReward              = 1.00;
input string          InpStartupLogFileName      = "forex_session_breakout_startup_log.csv";
input string          InpSignalLogFileName       = "forex_session_breakout_signal_log.csv";
input string          InpOrderLogFileName        = "forex_session_breakout_order_log.csv";
input string          InpManagementLogFileName   = "forex_session_breakout_management_log.csv";
input string          InpOrderComment            = "FX_SESSION_BREAKOUT";

CTrade   g_trade;
int      g_atr_handle = INVALID_HANDLE;
int      g_daily_atr_handle = INVALID_HANDLE;
datetime g_last_signal_bar = 0;
datetime g_last_trade_time = 0;
string   g_trade_day = "";
int      g_trades_today = 0;

string Timestamp()
  {
   return TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
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

void AppendCsvLine(const string file_name, const string header, const string &values[])
  {
   const bool exists = FileIsExist(file_name);
   const int handle = FileOpen(file_name, FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI);
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("FOREX_SESSION_BREAKOUT: failed to open log %s err=%d", file_name, GetLastError());
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
   ArrayResize(values, 13);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = AccountInfoString(ACCOUNT_SERVER);
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = BoolText((bool)MQLInfoInteger(MQL_TESTER));
   values[7] = IntegerToString((int)InpSignalTimeframe);
   values[8] = IntegerToString((int)InpDirectionMode);
   values[9] = IntegerToString(InpRangeStartHour) + ":" + IntegerToString(InpRangeStartMinute);
   values[10] = IntegerToString(InpRangeMinutes);
   values[11] = status;
   values[12] = detail;
   AppendCsvLine(
      InpStartupLogFileName,
      "timestamp_broker,run_id,server,account,symbol,magic,is_tester,signal_timeframe,direction_mode,range_start,range_minutes,status,detail",
      values
   );
  }

void LogSignal(
   const string direction,
   const string reason,
   const datetime bar_time,
   const double open_price,
   const double high_price,
   const double low_price,
   const double close_price,
   const double atr,
   const double range_high,
   const double range_low,
   const double range_atr,
   const double body_fraction,
   const double close_location,
   const long spread_points
)
  {
   string values[];
   ArrayResize(values, 20);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[3] = _Symbol;
   values[4] = direction;
   values[5] = reason;
   values[6] = TimeToString(bar_time, TIME_DATE | TIME_SECONDS);
   values[7] = DoubleToString(open_price, _Digits);
   values[8] = DoubleToString(high_price, _Digits);
   values[9] = DoubleToString(low_price, _Digits);
   values[10] = DoubleToString(close_price, _Digits);
   values[11] = DoubleToString(atr, _Digits);
   values[12] = DoubleToString(range_high, _Digits);
   values[13] = DoubleToString(range_low, _Digits);
   values[14] = DoubleToString(range_atr, 4);
   values[15] = DoubleToString(body_fraction, 4);
   values[16] = DoubleToString(close_location, 4);
   values[17] = IntegerToString((int)spread_points);
   values[18] = IntegerToString((int)InpSignalTimeframe);
   values[19] = "";
   AppendCsvLine(
      InpSignalLogFileName,
      "timestamp_broker,run_id,account,symbol,direction,reason,bar_time,open,high,low,close,atr,range_high,range_low,range_atr,body_fraction,close_location,spread_points,signal_timeframe,extra",
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
   ArrayResize(values, 18);
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
   AppendCsvLine(
      InpOrderLogFileName,
      "timestamp_broker,run_id,account,symbol,magic,action,direction,lots,bid,ask,spread_points,sl,tp,stop_points,retcode,retcode_description,order_ticket,deal_and_reason",
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

datetime DayStart(const datetime value)
  {
   MqlDateTime parts;
   TimeToStruct(value, parts);
   parts.hour = 0;
   parts.min = 0;
   parts.sec = 0;
   return StructToTime(parts);
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

bool BuildSessionRange(
   const datetime bar_time,
   double &range_high,
   double &range_low,
   datetime &range_start,
   datetime &range_end,
   datetime &trade_start,
   datetime &trade_end
)
  {
   range_high = 0.0;
   range_low = 0.0;
   const datetime day_start = DayStart(bar_time);
   range_start = day_start + InpRangeStartHour * 3600 + InpRangeStartMinute * 60;
   range_end = range_start + InpRangeMinutes * 60;
   if(InpTradeStartHour >= 0)
      trade_start = day_start + InpTradeStartHour * 3600 + InpTradeStartMinute * 60;
   else
      trade_start = range_end;
   trade_end = trade_start + InpTradeWindowMinutes * 60;
   if(bar_time < trade_start || bar_time >= trade_end)
      return false;

   for(int shift = 1; shift < 600; shift++)
     {
      const datetime t = iTime(InpTargetSymbol, InpSignalTimeframe, shift);
      if(t == 0)
         break;
      if(t < range_start)
         break;
      if(t >= range_start && t < range_end)
        {
         const double high = iHigh(InpTargetSymbol, InpSignalTimeframe, shift);
         const double low = iLow(InpTargetSymbol, InpSignalTimeframe, shift);
         if(high <= 0.0 || low <= 0.0)
            continue;
         if(range_high == 0.0 || high > range_high)
            range_high = high;
         if(range_low == 0.0 || low < range_low)
            range_low = low;
        }
     }
   return range_high > range_low && range_low > 0.0;
  }

bool BuildSignal(
   string &direction,
   string &reason,
   const datetime bar_time,
   const double open_price,
   const double high_price,
   const double low_price,
   const double close_price,
   const double atr,
   double &range_high,
   double &range_low,
   double &range_atr,
   double &body_fraction,
   double &close_location
)
  {
   direction = "";
   reason = "";
   datetime range_start = 0;
   datetime range_end = 0;
   datetime trade_start = 0;
   datetime trade_end = 0;
   if(!BuildSessionRange(bar_time, range_high, range_low, range_start, range_end, trade_start, trade_end))
      return false;

   const double bar_range = MathMax(high_price - low_price, _Point);
   body_fraction = MathAbs(close_price - open_price) / bar_range;
   close_location = (close_price - low_price) / bar_range;
   const double session_range = range_high - range_low;
   range_atr = atr > 0.0 ? session_range / atr : 0.0;
   if(atr <= 0.0 || range_atr < InpMinRangeAtr || (InpMaxRangeAtr > 0.0 && range_atr > InpMaxRangeAtr))
      return false;
   if(InpMinDailyRangeAtrFraction > 0.0)
     {
      if(g_daily_atr_handle == INVALID_HANDLE)
         return false;
      double daily_atr = 0.0;
      if(!CopyOne(g_daily_atr_handle, 0, 1, daily_atr) || daily_atr <= 0.0)
         return false;
      if(session_range / daily_atr < InpMinDailyRangeAtrFraction)
         return false;
     }
   if(InpMinBodyFraction > 0.0 && body_fraction < InpMinBodyFraction)
      return false;

   const double buffer = InpBreakoutBufferAtr * atr;
   if(close_price > range_high + buffer && close_location >= InpLongCloseLocation)
     {
      direction = "LONG";
      reason = "SESSION_RANGE_BREAK_LONG";
     }
   else if(close_price < range_low - buffer && close_location <= InpShortCloseLocation)
     {
      direction = "SHORT";
      reason = "SESSION_RANGE_BREAK_SHORT";
     }
   return direction != "";
  }

void EvaluateCompletedSignalBar()
  {
   UpdateTradeDay();
   if(iBars(InpTargetSymbol, InpSignalTimeframe) < 100)
      return;

   double atr = 0.0;
   if(!CopyOne(g_atr_handle, 0, 1, atr) || atr <= 0.0)
      return;

   const datetime bar_time = iTime(InpTargetSymbol, InpSignalTimeframe, 1);
   const double open_price = iOpen(InpTargetSymbol, InpSignalTimeframe, 1);
   const double high_price = iHigh(InpTargetSymbol, InpSignalTimeframe, 1);
   const double low_price = iLow(InpTargetSymbol, InpSignalTimeframe, 1);
   const double close_price = iClose(InpTargetSymbol, InpSignalTimeframe, 1);
   if(bar_time == 0 || open_price <= 0.0 || high_price <= 0.0 || low_price <= 0.0 || close_price <= 0.0)
      return;

   string direction = "";
   string reason = "";
   double range_high = 0.0;
   double range_low = 0.0;
   double range_atr = 0.0;
   double body_fraction = 0.0;
   double close_location = 0.0;
   if(!BuildSignal(direction, reason, bar_time, open_price, high_price, low_price, close_price, atr, range_high, range_low, range_atr, body_fraction, close_location))
      return;

   const long spread_points = SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD);
   LogSignal(direction, reason, bar_time, open_price, high_price, low_price, close_price, atr, range_high, range_low, range_atr, body_fraction, close_location, spread_points);

   const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
   const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
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

   double stop_distance = MathMax(InpStopAtrMultiple * atr, InpStopRangeMultiple * (range_high - range_low));
   stop_distance = MathMax(stop_distance, InpStopFloorPoints * _Point);
   double sl = 0.0;
   double tp = 0.0;
   double stop_points = 0.0;
   if(direction == "LONG")
     {
      sl = NormalizeDouble(MathMin(range_low, ask - stop_distance), _Digits);
      stop_distance = ask - sl;
      stop_points = stop_distance / _Point;
      tp = NormalizeDouble(ask + InpRiskReward * stop_distance, _Digits);
     }
   else
     {
      sl = NormalizeDouble(MathMax(range_high, bid + stop_distance), _Digits);
      stop_distance = sl - bid;
      stop_points = stop_distance / _Point;
      tp = NormalizeDouble(bid - InpRiskReward * stop_distance, _Digits);
     }
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

   bool sent = false;
   if(direction == "LONG")
      sent = g_trade.Buy(lots, InpTargetSymbol, 0.0, sl, tp, InpOrderComment);
   else
      sent = g_trade.Sell(lots, InpTargetSymbol, 0.0, sl, tp, InpOrderComment);
   LogOrder(sent ? "ORDER_SEND_OK" : "ORDER_SEND_FAIL", direction, sent ? "entered" : "order_send_failed", lots, bid, ask, spread_points, sl, tp, stop_points, (long)g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription(), g_trade.ResultOrder(), g_trade.ResultDeal(), g_trade.ResultPrice());
   if(sent)
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
   if(g_atr_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_INDICATOR_HANDLE", "atr_invalid");
      return INIT_FAILED;
     }
   if(InpMinDailyRangeAtrFraction > 0.0)
     {
      g_daily_atr_handle = iATR(InpTargetSymbol, PERIOD_D1, InpAtrPeriod);
      if(g_daily_atr_handle == INVALID_HANDLE)
        {
         LogStartup("INIT_FAILED_INDICATOR_HANDLE", "daily_atr_invalid");
         return INIT_FAILED;
        }
     }
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   LogStartup("INIT_OK", "tester_only");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(g_atr_handle != INVALID_HANDLE)
      IndicatorRelease(g_atr_handle);
   if(g_daily_atr_handle != INVALID_HANDLE)
      IndicatorRelease(g_daily_atr_handle);
  }

void OnTick()
  {
   const datetime current_bar = iTime(InpTargetSymbol, InpSignalTimeframe, 0);
   if(current_bar == 0 || current_bar == g_last_signal_bar)
      return;
   g_last_signal_bar = current_bar;
   EvaluateCompletedSignalBar();
  }
