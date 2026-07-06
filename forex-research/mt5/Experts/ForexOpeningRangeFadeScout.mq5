//+------------------------------------------------------------------+
//| ForexOpeningRangeFadeScout.mq5                                    |
//| Tester-only M5 opening-range fade scout for Forex frequency work.  |
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

input string        InpRunId                    = "FOREX_OR_FADE_SCOUT";
input string        InpTargetSymbol             = "EURUSD";
input long          InpMagicNumber              = 26070501;
input DirectionMode InpDirectionMode            = DIR_BOTH;
input double        InpFixedLots                = 0.01;
input int           InpDeviationPoints          = 30;
input int           InpMaxSpreadPoints          = 100;
input int           InpMaxTradesPerDay          = 20;
input int           InpOpeningRangeStartHour    = 7;
input int           InpOpeningRangeMinutes      = 60;
input int           InpOpeningTradeWindowHours  = 5;
input double        InpOpeningBreakAtrMultiple  = 0.10;
input int           InpAtrPeriod                = 14;
input double        InpMinRangeAtr              = 0.50;
input double        InpMinBodyFraction          = 0.40;
input double        InpLongCloseLocation        = 0.68;
input double        InpShortCloseLocation       = 0.32;
input double        InpMinThreeBarMoveAtr       = 0.50;
input double        InpStopAtrMultiple          = 1.40;
input int           InpStopFloorPoints          = 30;
input int           InpStopCeilingPoints        = 700;
input double        InpRiskReward               = 1.00;
input string        InpStartupLogFileName       = "forex_or_fade_startup_log.csv";
input string        InpSignalLogFileName        = "forex_or_fade_signal_log.csv";
input string        InpOrderLogFileName         = "forex_or_fade_order_log.csv";
input string        InpOrderComment             = "FX_OR_FADE";

CTrade   g_trade;
int      g_atr_handle = INVALID_HANDLE;
datetime g_last_m5_bar = 0;
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
      PrintFormat("FOREX_OR_FADE: failed to open log %s err=%d", file_name, GetLastError());
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
   ArrayResize(values, 10);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = AccountInfoString(ACCOUNT_SERVER);
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = BoolText((bool)MQLInfoInteger(MQL_TESTER));
   values[7] = IntegerToString((int)InpDirectionMode);
   values[8] = status;
   values[9] = detail;
   AppendCsvLine(
      InpStartupLogFileName,
      "timestamp_broker,run_id,server,account,symbol,magic,is_tester,direction_mode,status,detail",
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
   const double opening_high,
   const double opening_low,
   const double body_fraction,
   const double close_location,
   const double three_bar_move_atr,
   const long spread_points
)
  {
   string values[];
   ArrayResize(values, 18);
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
   values[11] = DoubleToString(opening_high, _Digits);
   values[12] = DoubleToString(opening_low, _Digits);
   values[13] = DoubleToString(body_fraction, 4);
   values[14] = DoubleToString(close_location, 4);
   values[15] = DoubleToString(three_bar_move_atr, 4);
   values[16] = IntegerToString((int)spread_points);
   values[17] = "";
   AppendCsvLine(
      InpSignalLogFileName,
      "timestamp_broker,run_id,account,symbol,direction,reason,open,high,low,close,atr,opening_high,opening_low,body_fraction,close_location,three_bar_move_atr,spread_points,extra",
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

bool ReadAtr(double &atr)
  {
   double buffer[];
   ArrayResize(buffer, 1);
   if(CopyBuffer(g_atr_handle, 0, 1, 1, buffer) != 1)
      return false;
   atr = buffer[0];
   return atr > 0.0;
  }

double RecentHigh(const int start_shift, const int count)
  {
   double value = 0.0;
   for(int shift = start_shift; shift < start_shift + count; shift++)
     {
      const double high = iHigh(InpTargetSymbol, PERIOD_M5, shift);
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
      const double low = iLow(InpTargetSymbol, PERIOD_M5, shift);
      if(low <= 0.0)
         continue;
      if(value == 0.0 || low < value)
         value = low;
     }
   return value;
  }

bool OpeningRangeForSignal(const datetime signal_time, double &range_high, double &range_low)
  {
   range_high = 0.0;
   range_low = 0.0;

   MqlDateTime parts;
   TimeToStruct(signal_time, parts);
   parts.hour = MathMax(0, MathMin(23, InpOpeningRangeStartHour));
   parts.min = 0;
   parts.sec = 0;
   const datetime range_start = StructToTime(parts);
   const datetime range_end = range_start + MathMax(5, InpOpeningRangeMinutes) * 60;
   const datetime trade_end = range_end + MathMax(1, InpOpeningTradeWindowHours) * 3600;
   if(signal_time < range_end || signal_time > trade_end)
      return false;

   const int bars = iBars(InpTargetSymbol, PERIOD_M5);
   int found = 0;
   for(int shift = 1; shift < bars && shift < 600; shift++)
     {
      const datetime bar_time = iTime(InpTargetSymbol, PERIOD_M5, shift);
      if(bar_time == 0)
         break;
      if(bar_time >= signal_time)
         continue;
      if(bar_time < range_start)
         break;
      if(bar_time >= range_start && bar_time < range_end)
        {
         const double bar_high = iHigh(InpTargetSymbol, PERIOD_M5, shift);
         const double bar_low = iLow(InpTargetSymbol, PERIOD_M5, shift);
         if(bar_high <= 0.0 || bar_low <= 0.0)
            continue;
         if(found == 0)
           {
            range_high = bar_high;
            range_low = bar_low;
           }
         else
           {
            range_high = MathMax(range_high, bar_high);
            range_low = MathMin(range_low, bar_low);
           }
         found++;
        }
     }
   return found >= MathMax(1, InpOpeningRangeMinutes / 5) && range_high > range_low;
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

void EvaluateCompletedM5Bar()
  {
   UpdateTradeDay();
   if(iBars(InpTargetSymbol, PERIOD_M5) < 100)
      return;

   const datetime signal_time = iTime(InpTargetSymbol, PERIOD_M5, 1);
   double opening_high = 0.0;
   double opening_low = 0.0;
   if(!OpeningRangeForSignal(signal_time, opening_high, opening_low))
      return;

   double atr = 0.0;
   if(!ReadAtr(atr))
      return;

   const double open_price = iOpen(InpTargetSymbol, PERIOD_M5, 1);
   const double high_price = iHigh(InpTargetSymbol, PERIOD_M5, 1);
   const double low_price = iLow(InpTargetSymbol, PERIOD_M5, 1);
   const double close_price = iClose(InpTargetSymbol, PERIOD_M5, 1);
   const double range = MathMax(high_price - low_price, _Point);
   const double body = MathAbs(close_price - open_price);
   const double body_fraction = body / range;
   const double close_location = (close_price - low_price) / range;
   const double close0 = iClose(InpTargetSymbol, PERIOD_M5, 4);
   const double three_bar_move_atr = atr > 0.0 ? (close_price - close0) / atr : 0.0;

   const bool up_break =
      close_price >= opening_high + InpOpeningBreakAtrMultiple * atr &&
      close_price > open_price &&
      range >= InpMinRangeAtr * atr &&
      body_fraction >= InpMinBodyFraction &&
      close_location >= InpLongCloseLocation &&
      three_bar_move_atr >= InpMinThreeBarMoveAtr;
   const bool down_break =
      close_price <= opening_low - InpOpeningBreakAtrMultiple * atr &&
      close_price < open_price &&
      range >= InpMinRangeAtr * atr &&
      body_fraction >= InpMinBodyFraction &&
      close_location <= InpShortCloseLocation &&
      three_bar_move_atr <= -InpMinThreeBarMoveAtr;

   string direction = "";
   string reason = "";
   if(up_break)
     {
      direction = "SHORT";
      reason = "M5_OPENING_RANGE_FADE_UP_BREAK_SHORT";
     }
   else if(down_break)
     {
      direction = "LONG";
      reason = "M5_OPENING_RANGE_FADE_DOWN_BREAK_LONG";
     }
   else
      return;

   const long spread_points = SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD);
   LogSignal(direction, reason, open_price, high_price, low_price, close_price, atr, opening_high, opening_low, body_fraction, close_location, three_bar_move_atr, spread_points);

   if(!DirectionModeAllows(direction))
     {
      LogOrder("GUARD_BLOCK", direction, "direction_mode_block", 0.0, SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID), SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK), spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(CountOwnOpenPositions() > 0)
     {
      LogOrder("GUARD_BLOCK", direction, "own_position_exists", 0.0, SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID), SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK), spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(spread_points > InpMaxSpreadPoints)
     {
      LogOrder("GUARD_BLOCK", direction, "spread_too_high", 0.0, SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID), SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK), spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(InpMaxTradesPerDay > 0 && g_trades_today >= InpMaxTradesPerDay)
     {
      LogOrder("GUARD_BLOCK", direction, "daily_trade_cap", 0.0, SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID), SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK), spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
     {
      LogOrder("GUARD_BLOCK", direction, "terminal_or_account_trading_disabled", 0.0, SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID), SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK), spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }

   const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
   const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
   double stop_distance = MathMax(InpStopAtrMultiple * atr, InpStopFloorPoints * _Point);
   const double stop_points = stop_distance / _Point;
   if(InpStopCeilingPoints > 0 && stop_points > InpStopCeilingPoints)
     {
      LogOrder("GUARD_BLOCK", direction, "stop_ceiling_exceeded", 0.0, bid, ask, spread_points, 0.0, 0.0, stop_points, 0, "", 0, 0, 0.0);
      return;
     }
   const double lots = NormalizeVolume(InpFixedLots);
   if(lots <= 0.0)
     {
      LogOrder("GUARD_BLOCK", direction, "invalid_lots", 0.0, bid, ask, spread_points, 0.0, 0.0, stop_points, 0, "", 0, 0, 0.0);
      return;
     }

   bool sent = false;
   double sl = 0.0;
   double tp = 0.0;
   if(direction == "LONG")
     {
      sl = NormalizeDouble(ask - stop_distance, _Digits);
      tp = NormalizeDouble(ask + InpRiskReward * stop_distance, _Digits);
      sent = g_trade.Buy(lots, InpTargetSymbol, 0.0, sl, tp, InpOrderComment);
     }
   else
     {
      sl = NormalizeDouble(bid + stop_distance, _Digits);
      tp = NormalizeDouble(bid - InpRiskReward * stop_distance, _Digits);
      sent = g_trade.Sell(lots, InpTargetSymbol, 0.0, sl, tp, InpOrderComment);
     }
   LogOrder(sent ? "ORDER_SEND_OK" : "ORDER_SEND_FAIL", direction, sent ? "entered" : "order_send_failed", lots, bid, ask, spread_points, sl, tp, stop_points, (long)g_trade.ResultRetcode(), g_trade.ResultRetcodeDescription(), g_trade.ResultOrder(), g_trade.ResultDeal(), g_trade.ResultPrice());
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
   g_atr_handle = iATR(InpTargetSymbol, PERIOD_M5, InpAtrPeriod);
   if(g_atr_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_ATR_HANDLE", "invalid_atr");
      return INIT_FAILED;
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
  }

void OnTick()
  {
   const datetime current_m5 = iTime(InpTargetSymbol, PERIOD_M5, 0);
   if(current_m5 == 0 || current_m5 == g_last_m5_bar)
      return;
   g_last_m5_bar = current_m5;
   EvaluateCompletedM5Bar();
  }
