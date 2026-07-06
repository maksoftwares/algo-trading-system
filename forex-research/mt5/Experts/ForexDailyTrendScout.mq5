//+------------------------------------------------------------------+
//| ForexDailyTrendScout.mq5                                         |
//| Tester-only D1 breakout/trend-following scout for Forex research. |
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

input string        InpRunId                 = "FOREX_DAILY_TREND_SCOUT";
input string        InpTargetSymbol          = "EURUSD";
input long          InpMagicNumber           = 26070851;
input DirectionMode InpDirectionMode         = DIR_BOTH;
input double        InpFixedLots             = 0.01;
input int           InpDeviationPoints       = 30;
input int           InpMaxSpreadPoints       = 100;
input int           InpMaxTradesPerDay       = 1;
input string        InpBlockedEntryHoursCsv  = "";
input int           InpLookbackDays          = 40;
input int           InpAtrPeriod             = 14;
input double        InpInitialStopAtr        = 2.00;
input double        InpTrailStopAtr          = 3.00;
input int           InpStopFloorPoints       = 30;
input int           InpStopCeilingPoints     = 5000;
input int           InpMaxHoldingDays        = 120;
input string        InpStartupLogFileName    = "forex_daily_trend_startup_log.csv";
input string        InpSignalLogFileName     = "forex_daily_trend_signal_log.csv";
input string        InpOrderLogFileName      = "forex_daily_trend_order_log.csv";
input string        InpManagementLogFileName = "forex_daily_trend_management_log.csv";
input string        InpOrderComment          = "FX_DAILY_TREND";

CTrade   g_trade;
int      g_atr_handle = INVALID_HANDLE;
datetime g_last_d1_bar = 0;
string   g_trade_day = "";
int      g_trades_today = 0;

string Timestamp()
  {
   return TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
  }

int HourOf(const datetime value)
  {
   MqlDateTime parts;
   TimeToStruct(value, parts);
   return parts.hour;
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
      PrintFormat("FOREX_DAILY_TREND: failed to open log %s err=%d", file_name, GetLastError());
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
   ArrayResize(values, 12);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = AccountInfoString(ACCOUNT_SERVER);
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = BoolText((bool)MQLInfoInteger(MQL_TESTER));
   values[7] = IntegerToString((int)InpDirectionMode);
   values[8] = IntegerToString(InpLookbackDays);
   values[9] = DoubleToString(InpInitialStopAtr, 2);
   values[10] = status;
   values[11] = detail;
   AppendCsvLine(
      InpStartupLogFileName,
      "timestamp_broker,run_id,server,account,symbol,magic,is_tester,direction_mode,lookback_days,initial_stop_atr,status,detail",
      values
   );
  }

void LogSignal(
   const string direction,
   const string reason,
   const datetime bar_time,
   const double close_price,
   const double breakout_level,
   const double atr,
   const long spread_points
)
  {
   string values[];
   ArrayResize(values, 12);
   values[0] = Timestamp();
   values[1] = TimeToString(bar_time, TIME_DATE | TIME_SECONDS);
   values[2] = InpRunId;
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = InpTargetSymbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = direction;
   values[7] = reason;
   values[8] = DoubleToString(close_price, _Digits);
   values[9] = DoubleToString(breakout_level, _Digits);
   values[10] = DoubleToString(atr, _Digits);
   values[11] = IntegerToString((int)spread_points);
   AppendCsvLine(
      InpSignalLogFileName,
      "timestamp_broker,signal_bar_time,run_id,account,symbol,magic,direction,reason,close,breakout_level,atr,spread_points",
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
   const ulong order_id,
   const ulong deal_id,
   const double result_price
)
  {
   string values[];
   ArrayResize(values, 18);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = InpTargetSymbol;
   values[3] = direction;
   values[4] = IntegerToString((int)InpMagicNumber);
   values[5] = action;
   values[6] = reason;
   values[7] = DoubleToString(lots, 2);
   values[8] = DoubleToString(bid, _Digits);
   values[9] = DoubleToString(ask, _Digits);
   values[10] = IntegerToString((int)spread_points);
   values[11] = DoubleToString(sl, _Digits);
   values[12] = DoubleToString(tp, _Digits);
   values[13] = DoubleToString(stop_points, 1);
   values[14] = IntegerToString((int)retcode);
   values[15] = retcode_description;
   values[16] = IntegerToString((int)order_id);
   values[17] = IntegerToString((int)deal_id) + "@" + DoubleToString(result_price, _Digits);
   AppendCsvLine(
      InpOrderLogFileName,
      "timestamp_broker,run_id,symbol,direction,magic,action,reason,lots,bid,ask,spread_points,sl,tp,stop_points,retcode,retcode_description,order_id,deal_price",
      values
   );
  }

void LogManagement(const string action, const string reason, const ulong ticket, const double old_sl, const double new_sl)
  {
   string values[];
   ArrayResize(values, 8);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = InpTargetSymbol;
   values[3] = IntegerToString((int)InpMagicNumber);
   values[4] = action;
   values[5] = reason;
   values[6] = IntegerToString((int)ticket);
   values[7] = DoubleToString(old_sl, _Digits) + "->" + DoubleToString(new_sl, _Digits);
   AppendCsvLine(
      InpManagementLogFileName,
      "timestamp_broker,run_id,symbol,magic,action,reason,ticket,sl_change",
      values
   );
  }

bool DirectionAllowed(const string direction)
  {
   if(InpDirectionMode == DIR_BOTH)
      return true;
   if(InpDirectionMode == DIR_LONG_ONLY && direction == "LONG")
      return true;
   if(InpDirectionMode == DIR_SHORT_ONLY && direction == "SHORT")
      return true;
   return false;
  }

bool IsBlockedHour(const int hour)
  {
   if(InpBlockedEntryHoursCsv == "")
      return false;
   string current = "";
   for(int i = 0; i <= StringLen(InpBlockedEntryHoursCsv); i++)
     {
      const ushort ch = (i < StringLen(InpBlockedEntryHoursCsv)) ? StringGetCharacter(InpBlockedEntryHoursCsv, i) : ',';
      if(ch == ',')
        {
         if(StringLen(current) > 0 && (int)StringToInteger(current) == hour)
            return true;
         current = "";
        }
      else if(ch >= '0' && ch <= '9')
         current += ShortToString(ch);
     }
   return false;
  }

double NormalizeVolume(const double lots)
  {
   const double min_lots = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MIN);
   const double max_lots = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_MAX);
   const double step = SymbolInfoDouble(InpTargetSymbol, SYMBOL_VOLUME_STEP);
   double value = MathMax(min_lots, MathMin(max_lots, lots));
   if(step > 0)
      value = MathFloor(value / step) * step;
   return NormalizeDouble(value, 2);
  }

bool HasOpenPosition()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetInteger(POSITION_MAGIC) == InpMagicNumber && PositionGetString(POSITION_SYMBOL) == InpTargetSymbol)
         return true;
     }
   return false;
  }

bool GetAtr(const int shift, double &atr)
  {
   double buffer[];
   ArraySetAsSeries(buffer, true);
   if(CopyBuffer(g_atr_handle, 0, shift, 1, buffer) != 1)
      return false;
   atr = buffer[0];
   return atr > 0.0;
  }

double HighestHigh(const int start_shift, const int count)
  {
   double value = -DBL_MAX;
   for(int shift = start_shift; shift < start_shift + count; shift++)
     {
      const double high = iHigh(InpTargetSymbol, PERIOD_D1, shift);
      if(high > value)
         value = high;
     }
   return value;
  }

double LowestLow(const int start_shift, const int count)
  {
   double value = DBL_MAX;
   for(int shift = start_shift; shift < start_shift + count; shift++)
     {
      const double low = iLow(InpTargetSymbol, PERIOD_D1, shift);
      if(low < value)
         value = low;
     }
   return value;
  }

void RefreshTradeDay()
  {
   const string day = TimeToString(TimeCurrent(), TIME_DATE);
   if(day != g_trade_day)
     {
      g_trade_day = day;
      g_trades_today = 0;
     }
  }

void ManageOpenPositions()
  {
   double atr = 0.0;
   if(!GetAtr(1, atr))
      return;
   const double completed_close = iClose(InpTargetSymbol, PERIOD_D1, 1);
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber || PositionGetString(POSITION_SYMBOL) != InpTargetSymbol)
         continue;

      const long type = PositionGetInteger(POSITION_TYPE);
      const double current_sl = PositionGetDouble(POSITION_SL);
      const double current_tp = PositionGetDouble(POSITION_TP);
      const datetime open_time = (datetime)PositionGetInteger(POSITION_TIME);
      if(InpMaxHoldingDays > 0 && TimeCurrent() - open_time >= InpMaxHoldingDays * 86400)
        {
         const bool closed = g_trade.PositionClose(ticket);
         LogManagement(closed ? "POSITION_CLOSE_OK" : "POSITION_CLOSE_FAIL", "max_holding_days", ticket, current_sl, current_sl);
         continue;
        }

      if(InpTrailStopAtr <= 0.0)
         continue;
      double new_sl = current_sl;
      if(type == POSITION_TYPE_BUY)
        {
         const double candidate = NormalizeDouble(completed_close - InpTrailStopAtr * atr, _Digits);
         if(current_sl == 0.0 || candidate > current_sl + _Point)
            new_sl = candidate;
        }
      else if(type == POSITION_TYPE_SELL)
        {
         const double candidate = NormalizeDouble(completed_close + InpTrailStopAtr * atr, _Digits);
         if(current_sl == 0.0 || candidate < current_sl - _Point)
            new_sl = candidate;
        }
      if(new_sl != current_sl)
        {
         const bool modified = g_trade.PositionModify(ticket, new_sl, current_tp);
         LogManagement(modified ? "TRAIL_MODIFY_OK" : "TRAIL_MODIFY_FAIL", "d1_atr_trail", ticket, current_sl, new_sl);
        }
     }
  }

void TryEnterDailyBreakout()
  {
   RefreshTradeDay();
   const datetime signal_bar_time = iTime(InpTargetSymbol, PERIOD_D1, 1);
   if(signal_bar_time == 0 || signal_bar_time == g_last_d1_bar)
      return;
   g_last_d1_bar = signal_bar_time;

   if(iBars(InpTargetSymbol, PERIOD_D1) < InpLookbackDays + InpAtrPeriod + 5)
      return;

   ManageOpenPositions();
   if(HasOpenPosition())
      return;

   const long spread_points = SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD);
   const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
   const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
   if(spread_points > InpMaxSpreadPoints)
     {
      LogSignal("NONE", "spread_too_wide", signal_bar_time, iClose(InpTargetSymbol, PERIOD_D1, 1), 0.0, 0.0, spread_points);
      return;
     }
   if(InpMaxTradesPerDay > 0 && g_trades_today >= InpMaxTradesPerDay)
      return;
   if(IsBlockedHour(HourOf(TimeCurrent())))
      return;

   double atr = 0.0;
   if(!GetAtr(1, atr))
      return;
   const double close_price = iClose(InpTargetSymbol, PERIOD_D1, 1);
   const double high_break = HighestHigh(2, InpLookbackDays);
   const double low_break = LowestLow(2, InpLookbackDays);
   string direction = "NONE";
   double breakout_level = 0.0;
   if(close_price > high_break)
     {
      direction = "LONG";
      breakout_level = high_break;
     }
   else if(close_price < low_break)
     {
      direction = "SHORT";
      breakout_level = low_break;
     }
   else
     {
      LogSignal("NONE", "no_d1_breakout", signal_bar_time, close_price, high_break, atr, spread_points);
      return;
     }

   LogSignal(direction, "d1_close_breakout", signal_bar_time, close_price, breakout_level, atr, spread_points);
   if(!DirectionAllowed(direction))
      return;

   double stop_distance = MathMax(InpInitialStopAtr * atr, InpStopFloorPoints * _Point);
   const double stop_points = stop_distance / _Point;
   if(InpStopCeilingPoints > 0 && stop_points > InpStopCeilingPoints)
     {
      LogOrder("ORDER_SKIP", direction, "stop_ceiling", 0.0, bid, ask, spread_points, 0.0, 0.0, stop_points, 0, "stop_ceiling", 0, 0, 0.0);
      return;
     }

   const double lots = NormalizeVolume(InpFixedLots);
   bool sent = false;
   double sl = 0.0;
   if(direction == "LONG")
     {
      sl = NormalizeDouble(ask - stop_distance, _Digits);
      sent = g_trade.Buy(lots, InpTargetSymbol, 0.0, sl, 0.0, InpOrderComment);
     }
   else
     {
      sl = NormalizeDouble(bid + stop_distance, _Digits);
      sent = g_trade.Sell(lots, InpTargetSymbol, 0.0, sl, 0.0, InpOrderComment);
     }
   LogOrder(sent ? "ORDER_SEND_OK" : "ORDER_SEND_FAIL", direction, sent ? "entered" : "order_send_failed", lots, bid, ask, spread_points, sl, 0.0, stop_points, (long)g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription(), g_trade.ResultOrder(), g_trade.ResultDeal(), g_trade.ResultPrice());
   if(sent)
      g_trades_today++;
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
   g_atr_handle = iATR(InpTargetSymbol, PERIOD_D1, InpAtrPeriod);
   if(g_atr_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_INDICATOR_HANDLE", "d1_atr_invalid");
      return INIT_FAILED;
     }
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   LogStartup("INIT_OK", "tester_only_d1_breakout");
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(g_atr_handle != INVALID_HANDLE)
      IndicatorRelease(g_atr_handle);
  }

void OnTick()
  {
   TryEnterDailyBreakout();
  }
