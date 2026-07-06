//+------------------------------------------------------------------+
//| ForexBondVolAsiaCarryReliefV1.mq5                                 |
//| Tester-only USDJPY H4 MOVE bond-vol Asia-session pullback clue.    |
//| OnInit fails outside MQL_TESTER; this is not a runtime/demo EA.     |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - forex research lane"
#property version   "1.000"
#property strict
#property tester_file "forex_bond_vol_context.csv"

#include <Trade/Trade.mqh>

input string InpRunId                    = "FOREX_BOND_VOL_ASIA_CARRY_RELIEF_V1";
input string InpTargetSymbol             = "USDJPY";
input long   InpMagicNumber              = 26070302;
input double InpFixedLots                = 0.01;
input int    InpDeviationPoints          = 20;
input int    InpMaxSpreadPoints          = 0;
input int    InpMinStopPoints            = 5;
input double InpTargetR                  = 1.35;
input int    InpMaxHoldH4Bars            = 14;
input int    InpAtrPeriod                = 14;
input int    InpEmaFastPeriod            = 20;
input int    InpEmaMidPeriod             = 50;
input int    InpEmaSlowPeriod            = 100;
input int    InpWarmupBars               = 260;
input int    InpServerUtcOffsetHours     = 0;
input string InpContextCsvFileName       = "forex_bond_vol_context.csv";
input string InpStartupLogFileName       = "forex_bond_vol_startup_log.csv";
input string InpSignalLogFileName        = "forex_bond_vol_signal_log.csv";
input string InpOrderLogFileName         = "forex_bond_vol_order_log.csv";
input string InpOrderComment             = "FX_BOND_VOL_V1";

struct ContextRow
  {
   long   available_epoch;
   double move_5d_pct;
   double move_20d_pct;
   double move_z60;
  };

CTrade    g_trade;
ContextRow g_context[];
int       g_atr_handle = INVALID_HANDLE;
int       g_ema20_handle = INVALID_HANDLE;
int       g_ema50_handle = INVALID_HANDLE;
int       g_ema100_handle = INVALID_HANDLE;
datetime  g_last_h4_bar = 0;

string BoolText(const bool value) { return value ? "true" : "false"; }

string Timestamp()
  {
   return TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
  }

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
      PrintFormat("FOREX_BOND_VOL_V1: failed to open log %s err=%d", file_name, GetLastError());
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
   ArrayResize(values, 11);
   values[0] = Timestamp();
   values[1] = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   values[2] = InpRunId;
   values[3] = AccountInfoString(ACCOUNT_SERVER);
   values[4] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[5] = _Symbol;
   values[6] = IntegerToString((int)InpMagicNumber);
   values[7] = BoolText((bool)MQLInfoInteger(MQL_TESTER));
   values[8] = IntegerToString(InpServerUtcOffsetHours);
   values[9] = status;
   values[10] = detail;
   AppendCsvLine(
      InpStartupLogFileName,
      "timestamp_broker,timestamp_local,run_id,server,account,symbol,magic,is_tester,server_utc_offset_hours,status,detail",
      values
   );
  }

void LogSignal(
   const string direction,
   const string reason,
   const datetime signal_bar_server,
   const datetime signal_bar_utc,
   const datetime entry_bar_server,
   const datetime entry_bar_utc,
   const double open_price,
   const double high_price,
   const double low_price,
   const double close_price,
   const double atr_price,
   const double ema20,
   const double ema50,
   const double ema100,
   const double move_5d,
   const double move_20d,
   const double move_z,
   const double recent_extreme,
   const double stop_price,
   const long spread_points
)
  {
   string values[];
   ArrayResize(values, 25);
   values[0] = Timestamp();
   values[1] = InpRunId;
   values[2] = AccountInfoString(ACCOUNT_SERVER);
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = direction;
   values[6] = "SIGNAL";
   values[7] = reason;
   values[8] = TimeToString(signal_bar_server, TIME_DATE | TIME_MINUTES);
   values[9] = TimeToString(signal_bar_utc, TIME_DATE | TIME_MINUTES);
   values[10] = TimeToString(entry_bar_server, TIME_DATE | TIME_MINUTES);
   values[11] = TimeToString(entry_bar_utc, TIME_DATE | TIME_MINUTES);
   values[12] = DoubleToString(open_price, _Digits);
   values[13] = DoubleToString(high_price, _Digits);
   values[14] = DoubleToString(low_price, _Digits);
   values[15] = DoubleToString(close_price, _Digits);
   values[16] = DoubleToString(atr_price, _Digits);
   values[17] = DoubleToString(ema20, _Digits);
   values[18] = DoubleToString(ema50, _Digits);
   values[19] = DoubleToString(ema100, _Digits);
   values[20] = DoubleToString(move_5d, 4);
   values[21] = DoubleToString(move_20d, 4);
   values[22] = DoubleToString(move_z, 4);
   values[23] = DoubleToString(recent_extreme, _Digits);
   values[24] = DoubleToString(stop_price, _Digits) + "|spread_points=" + IntegerToString((int)spread_points);
   AppendCsvLine(
      InpSignalLogFileName,
      "timestamp_broker,run_id,server,account,symbol,direction,stage,reason,signal_bar_server,signal_bar_utc,entry_bar_server,entry_bar_utc,open,high,low,close,atr_price,ema20,ema50,ema100,move_5d_pct,move_20d_pct,move_z60,recent_extreme,stop_and_spread",
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
   const double entry_reference,
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
   values[1] = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   values[2] = InpRunId;
   values[3] = IntegerToString((int)AccountInfoInteger(ACCOUNT_LOGIN));
   values[4] = _Symbol;
   values[5] = IntegerToString((int)InpMagicNumber);
   values[6] = action;
   values[7] = direction;
   values[8] = DoubleToString(lots, 2);
   values[9] = DoubleToString(bid, _Digits);
   values[10] = DoubleToString(ask, _Digits);
   values[11] = IntegerToString((int)spread_points);
   values[12] = DoubleToString(entry_reference, _Digits);
   values[13] = DoubleToString(sl, _Digits);
   values[14] = DoubleToString(tp, _Digits);
   values[15] = DoubleToString(stop_points, 2);
   values[16] = IntegerToString((int)retcode);
   values[17] = retcode_description;
   values[18] = IntegerToString((int)order_ticket);
   values[19] = IntegerToString((int)deal_ticket) + "|result_price=" + DoubleToString(result_price, _Digits) + "|reason=" + reason;
   AppendCsvLine(
      InpOrderLogFileName,
      "timestamp_broker,timestamp_local,run_id,account,symbol,magic,action,direction,lots,bid,ask,spread_points,entry_reference,sl,tp,stop_points,retcode,retcode_description,order_ticket,deal_and_reason",
      values
   );
  }

datetime ServerToUtc(const datetime server_time)
  {
   return (datetime)((long)server_time - (long)InpServerUtcOffsetHours * 3600);
  }

int HourOf(const datetime value)
  {
   MqlDateTime parts;
   TimeToStruct(value, parts);
   return parts.hour;
  }

string SessionBucket(const int hour_utc)
  {
   if(hour_utc >= 0 && hour_utc <= 5)
      return "asia";
   if(hour_utc >= 6 && hour_utc <= 11)
      return "london";
   if(hour_utc >= 12 && hour_utc <= 16)
      return "ny_morning";
   if(hour_utc >= 17 && hour_utc <= 21)
      return "ny_late";
   return "rollover";
  }

bool ReadDoubleField(const int handle, double &value)
  {
   if(FileIsEnding(handle))
      return false;
   const string raw = FileReadString(handle);
   value = StringToDouble(raw);
   return raw != "";
  }

bool LoadContext()
  {
   const int handle = FileOpen(InpContextCsvFileName, FILE_READ | FILE_CSV | FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_CONTEXT_OPEN", InpContextCsvFileName + " err=" + IntegerToString(GetLastError()));
      return false;
     }
   for(int i = 0; i < 5 && !FileIsEnding(handle); i++)
      FileReadString(handle);

   ArrayResize(g_context, 0);
   while(!FileIsEnding(handle))
     {
      const string epoch_raw = FileReadString(handle);
      if(epoch_raw == "")
         break;
      double move_5d = 0.0;
      double move_20d = 0.0;
      double move_z = 0.0;
      if(!ReadDoubleField(handle, move_5d))
         break;
      if(!ReadDoubleField(handle, move_20d))
         break;
      if(!ReadDoubleField(handle, move_z))
         break;
      if(!FileIsEnding(handle))
         FileReadString(handle);

      const int next = ArraySize(g_context);
      ArrayResize(g_context, next + 1);
      g_context[next].available_epoch = (long)StringToInteger(epoch_raw);
      g_context[next].move_5d_pct = move_5d;
      g_context[next].move_20d_pct = move_20d;
      g_context[next].move_z60 = move_z;
     }
   FileClose(handle);

   if(ArraySize(g_context) <= 0)
     {
      LogStartup("INIT_FAILED_CONTEXT_EMPTY", InpContextCsvFileName);
      return false;
     }
   return true;
  }

bool LookupContext(const datetime signal_bar_utc, double &move_5d, double &move_20d, double &move_z)
  {
   const long epoch = (long)signal_bar_utc;
   int lo = 0;
   int hi = ArraySize(g_context) - 1;
   int best = -1;
   while(lo <= hi)
     {
      const int mid = (lo + hi) / 2;
      if(g_context[mid].available_epoch <= epoch)
        {
         best = mid;
         lo = mid + 1;
        }
      else
         hi = mid - 1;
     }
   if(best < 0)
      return false;
   move_5d = g_context[best].move_5d_pct;
   move_20d = g_context[best].move_20d_pct;
   move_z = g_context[best].move_z60;
   return true;
  }

bool CopyOne(const int handle, const int shift, double &value)
  {
   double buffer[];
   ArrayResize(buffer, 1);
   if(CopyBuffer(handle, 0, shift, 1, buffer) != 1)
      return false;
   value = buffer[0];
   return value != EMPTY_VALUE;
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

string DirectionFromPositionType(const ENUM_POSITION_TYPE type)
  {
   return type == POSITION_TYPE_BUY ? "LONG" : "SHORT";
  }

void ManageMaxHoldExits()
  {
   if(InpMaxHoldH4Bars <= 0)
      return;
   const int hold_seconds = InpMaxHoldH4Bars * PeriodSeconds(PERIOD_H4);
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      const ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || !PositionSelectByTicket(ticket))
         continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagicNumber || PositionGetString(POSITION_SYMBOL) != InpTargetSymbol)
         continue;
      const datetime entry_time = (datetime)PositionGetInteger(POSITION_TIME);
      if(TimeCurrent() - entry_time < hold_seconds)
         continue;
      const ENUM_POSITION_TYPE type = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
      const string direction = DirectionFromPositionType(type);
      const double volume = PositionGetDouble(POSITION_VOLUME);
      const double entry_price = PositionGetDouble(POSITION_PRICE_OPEN);
      const double sl = PositionGetDouble(POSITION_SL);
      const double tp = PositionGetDouble(POSITION_TP);
      const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
      const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
      const long spread_points = SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD);
      const bool closed = g_trade.PositionClose(ticket, InpDeviationPoints);
      LogOrder(
         closed ? "MAX_HOLD_CLOSE_OK" : "MAX_HOLD_CLOSE_FAIL",
         direction,
         "max_hold_exit",
         volume,
         bid,
         ask,
         spread_points,
         entry_price,
         sl,
         tp,
         0.0,
         (long)g_trade.ResultRetcode(),
         g_trade.ResultRetcodeDescription(),
         g_trade.ResultOrder(),
         g_trade.ResultDeal(),
         g_trade.ResultPrice()
      );
     }
  }

bool SendSignalOrder(const string direction, const double stop_price, const double close_price)
  {
   const double bid = SymbolInfoDouble(InpTargetSymbol, SYMBOL_BID);
   const double ask = SymbolInfoDouble(InpTargetSymbol, SYMBOL_ASK);
   const long spread_points = SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD);
   const double entry_reference = direction == "LONG" ? ask : bid;
   const double risk_distance = direction == "LONG" ? entry_reference - stop_price : stop_price - entry_reference;
   const double stop_points = risk_distance / _Point;
   if(CountOwnOpenPositions() > 0)
     {
      LogOrder("GUARD_BLOCK", direction, "own_position_exists", 0.0, bid, ask, spread_points, entry_reference, stop_price, 0.0, stop_points, 0, "", 0, 0, 0.0);
      return false;
     }
   if(InpMaxSpreadPoints > 0 && spread_points > InpMaxSpreadPoints)
     {
      LogOrder("GUARD_BLOCK", direction, "spread_too_high", 0.0, bid, ask, spread_points, entry_reference, stop_price, 0.0, stop_points, 0, "", 0, 0, 0.0);
      return false;
     }
   if(stop_points < InpMinStopPoints)
     {
      LogOrder("GUARD_BLOCK", direction, "stop_floor_rejected", 0.0, bid, ask, spread_points, entry_reference, stop_price, 0.0, stop_points, 0, "", 0, 0, 0.0);
      return false;
     }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
     {
      LogOrder("GUARD_BLOCK", direction, "terminal_or_account_trading_disabled", 0.0, bid, ask, spread_points, entry_reference, stop_price, 0.0, stop_points, 0, "", 0, 0, 0.0);
      return false;
     }
   const double lots = NormalizeVolume(InpFixedLots);
   if(lots <= 0.0)
     {
      LogOrder("GUARD_BLOCK", direction, "invalid_lots", 0.0, bid, ask, spread_points, entry_reference, stop_price, 0.0, stop_points, 0, "", 0, 0, 0.0);
      return false;
     }
   const double tp = direction == "LONG"
                     ? NormalizeDouble(ask + InpTargetR * risk_distance, _Digits)
                     : NormalizeDouble(bid - InpTargetR * risk_distance, _Digits);
   bool sent = false;
   if(direction == "LONG")
      sent = g_trade.Buy(lots, InpTargetSymbol, 0.0, stop_price, tp, InpOrderComment);
   else
      sent = g_trade.Sell(lots, InpTargetSymbol, 0.0, stop_price, tp, InpOrderComment);
   LogOrder(
      sent ? "ORDER_SEND_OK" : "ORDER_SEND_FAIL",
      direction,
      sent ? "entered" : "order_send_failed",
      lots,
      bid,
      ask,
      spread_points,
      entry_reference,
      stop_price,
      tp,
      stop_points,
      (long)g_trade.ResultRetcode(),
      g_trade.ResultRetcodeDescription(),
      g_trade.ResultOrder(),
      g_trade.ResultDeal(),
      g_trade.ResultPrice()
   );
   return sent;
  }

void EvaluateCompletedH4Bar()
  {
   if(iBars(InpTargetSymbol, PERIOD_H4) < InpWarmupBars + 10)
      return;

   const datetime signal_bar_server = iTime(InpTargetSymbol, PERIOD_H4, 1);
   const datetime entry_bar_server = iTime(InpTargetSymbol, PERIOD_H4, 0);
   if(signal_bar_server <= 0 || entry_bar_server <= 0)
      return;
   const datetime signal_bar_utc = ServerToUtc(signal_bar_server);
   const datetime entry_bar_utc = ServerToUtc(entry_bar_server);
   if(SessionBucket(HourOf(entry_bar_utc)) != "asia")
      return;

   double move_5d = 0.0;
   double move_20d = 0.0;
   double move_z = 0.0;
   if(!LookupContext(signal_bar_utc, move_5d, move_20d, move_z))
      return;

   double atr = 0.0;
   double ema20 = 0.0;
   double ema50 = 0.0;
   double ema100 = 0.0;
   if(!CopyOne(g_atr_handle, 1, atr) || !CopyOne(g_ema20_handle, 1, ema20) || !CopyOne(g_ema50_handle, 1, ema50) || !CopyOne(g_ema100_handle, 1, ema100))
      return;
   if(atr <= 0.0)
      return;

   const double open_price = iOpen(InpTargetSymbol, PERIOD_H4, 1);
   const double high_price = iHigh(InpTargetSymbol, PERIOD_H4, 1);
   const double low_price = iLow(InpTargetSymbol, PERIOD_H4, 1);
   const double close_price = iClose(InpTargetSymbol, PERIOD_H4, 1);
   const bool bond_vol_calm = move_5d <= -4.0 && move_20d <= -4.0 && move_z <= 0.25;
   const bool bond_vol_stress = move_5d >= 6.0 && move_z >= 0.50;
   string direction = "";
   string reason = "";
   double stop_price = 0.0;
   double recent_extreme = 0.0;

   if(bond_vol_calm && ema20 > ema50 && ema50 > ema100)
     {
      const bool touched = low_price <= ema20 + 0.25 * atr;
      const bool confirmed = close_price > open_price && close_price > ema20;
      if(!(touched && confirmed))
         return;
      recent_extreme = low_price;
      for(int shift = 2; shift <= 6; shift++)
         recent_extreme = MathMin(recent_extreme, iLow(InpTargetSymbol, PERIOD_H4, shift));
      stop_price = NormalizeDouble(MathMin(recent_extreme, close_price - 1.05 * atr), _Digits);
      direction = "LONG";
      reason = "H4_USDJPY_BOND_VOL_CALM_LONG";
     }
   else if(bond_vol_stress && ema20 < ema50 && ema50 < ema100)
     {
      const bool touched = high_price >= ema20 - 0.25 * atr;
      const bool confirmed = close_price < open_price && close_price < ema20;
      if(!(touched && confirmed))
         return;
      recent_extreme = high_price;
      for(int shift = 2; shift <= 6; shift++)
         recent_extreme = MathMax(recent_extreme, iHigh(InpTargetSymbol, PERIOD_H4, shift));
      stop_price = NormalizeDouble(MathMax(recent_extreme, close_price + 1.05 * atr), _Digits);
      direction = "SHORT";
      reason = "H4_USDJPY_BOND_VOL_STRESS_SHORT";
     }
   else
      return;

   const long spread_points = SymbolInfoInteger(InpTargetSymbol, SYMBOL_SPREAD);
   LogSignal(
      direction,
      reason,
      signal_bar_server,
      signal_bar_utc,
      entry_bar_server,
      entry_bar_utc,
      open_price,
      high_price,
      low_price,
      close_price,
      atr,
      ema20,
      ema50,
      ema100,
      move_5d,
      move_20d,
      move_z,
      recent_extreme,
      stop_price,
      spread_points
   );
   SendSignalOrder(direction, stop_price, close_price);
  }

int OnInit()
  {
   if(!MQLInfoInteger(MQL_TESTER))
     {
      LogStartup("INIT_FAILED_NOT_TESTER", "This EA is Strategy Tester only.");
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
   if(!LoadContext())
      return INIT_FAILED;

   g_atr_handle = iATR(InpTargetSymbol, PERIOD_H4, InpAtrPeriod);
   g_ema20_handle = iMA(InpTargetSymbol, PERIOD_H4, InpEmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_ema50_handle = iMA(InpTargetSymbol, PERIOD_H4, InpEmaMidPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_ema100_handle = iMA(InpTargetSymbol, PERIOD_H4, InpEmaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);
   if(g_atr_handle == INVALID_HANDLE || g_ema20_handle == INVALID_HANDLE || g_ema50_handle == INVALID_HANDLE || g_ema100_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_INDICATOR_HANDLE", "atr_or_ema_handle_invalid");
      return INIT_FAILED;
     }

   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   LogStartup("INIT_OK", "context_rows=" + IntegerToString(ArraySize(g_context)));
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(g_atr_handle != INVALID_HANDLE)
      IndicatorRelease(g_atr_handle);
   if(g_ema20_handle != INVALID_HANDLE)
      IndicatorRelease(g_ema20_handle);
   if(g_ema50_handle != INVALID_HANDLE)
      IndicatorRelease(g_ema50_handle);
   if(g_ema100_handle != INVALID_HANDLE)
      IndicatorRelease(g_ema100_handle);
  }

void OnTick()
  {
   ManageMaxHoldExits();
   const datetime current_h4 = iTime(InpTargetSymbol, PERIOD_H4, 0);
   if(current_h4 == 0 || current_h4 == g_last_h4_bar)
      return;
   g_last_h4_bar = current_h4;
   ManageMaxHoldExits();
   EvaluateCompletedH4Bar();
  }
