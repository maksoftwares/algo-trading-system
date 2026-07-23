//+------------------------------------------------------------------+
//| ForexMeanReversionScout.mq5                                       |
//| Tester-only M5 Bollinger/RSI mean-reversion scout for Forex.       |
//+------------------------------------------------------------------+
#property copyright "maksoftwares - forex research lane"
#property version   "1.000"
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

input string                  InpRunId                   = "FOREX_MEAN_REVERSION_SCOUT";
input string                  InpTargetSymbol            = "EURUSD";
input ENUM_TIMEFRAMES         InpSignalTimeframe         = PERIOD_M5;
input long                    InpMagicNumber             = 26070601;
input bool                    InpShadowMode              = true;
input bool                    InpEnableDemoOrders        = false;
input long                    InpAllowedAccountLogin     = 0;
input string                  InpExpectedServerMarker    = "Demo";
input bool                    InpUseH4TrendRiskOverlay   = false;
input double                  InpH4TrendAdditionalLots   = 0.01;
input double                  InpH4TrendAdxMinimum       = 22.0;
input double                  InpH4TrendEfficiencyMin    = 0.32;
input double                  InpH4TrendSlopeAtrMin      = 0.18;
input int                     InpH4VolatilityBaseline    = 504;
input double                  InpH4UnsafeAtrPercentile   = 0.95;
input double                  InpH4UnsafeGapAtr          = 1.50;
input MeanReversionSignalMode InpSignalMode              = MR_BB_CLOSE_FADE;
input DirectionMode           InpDirectionMode           = DIR_BOTH;
input double                  InpFixedLots               = 0.01;
input int                     InpDeviationPoints         = 30;
input int                     InpMaxSpreadPoints         = 100;
input int                     InpMaxTradesPerDay         = 24;
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
input double                  InpMinBodyFraction         = 0.00;
input double                  InpStopAtrMultiple         = 1.40;
input int                     InpStopFloorPoints         = 30;
input int                     InpStopCeilingPoints       = 700;
input double                  InpRiskReward              = 0.80;
input string                  InpStartupLogFileName      = "forex_meanrev_startup_log.csv";
input string                  InpSignalLogFileName       = "forex_meanrev_signal_log.csv";
input string                  InpOrderLogFileName        = "forex_meanrev_order_log.csv";
input string                  InpOrderComment            = "FX_MEANREV";

CTrade   g_trade;
int      g_atr_handle = INVALID_HANDLE;
int      g_bands_handle = INVALID_HANDLE;
int      g_rsi_handle = INVALID_HANDLE;
int      g_h4_atr_handle = INVALID_HANDLE;
int      g_h4_adx_handle = INVALID_HANDLE;
int      g_h4_ema_handle = INVALID_HANDLE;
datetime g_last_m5_bar = 0;
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
      PrintFormat("FOREX_MEANREV: failed to open log %s err=%d", file_name, GetLastError());
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
   values[7] = IntegerToString((int)InpSignalMode);
   values[8] = IntegerToString((int)InpDirectionMode);
   values[9] = DoubleToString(InpRiskReward, 2);
   values[10] = status;
   values[11] = detail;
   AppendCsvLine(
      InpStartupLogFileName,
      "timestamp_broker,run_id,server,account,symbol,magic,is_tester,signal_mode,direction_mode,risk_reward,status,detail",
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
   ArrayResize(values, 20);
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
   AppendCsvLine(
      InpSignalLogFileName,
      "timestamp_broker,run_id,account,symbol,direction,reason,open,high,low,close,atr,band_upper,band_mid,band_lower,rsi,body_fraction,band_distance_atr,spread_points,signal_mode,extra",
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

bool H4TrendRiskOverlayActive()
  {
   if(!InpUseH4TrendRiskOverlay)
      return false;
   double atr = 0.0;
   double adx = 0.0;
   double ema_now = 0.0;
   double ema_past = 0.0;
   if(!CopyOne(g_h4_atr_handle, 0, 1, atr) ||
      !CopyOne(g_h4_adx_handle, 0, 1, adx) ||
      !CopyOne(g_h4_ema_handle, 0, 1, ema_now) ||
      !CopyOne(g_h4_ema_handle, 0, 7, ema_past) ||
      atr <= 0.0)
      return false;

   const double close_now = iClose(InpTargetSymbol, PERIOD_H4, 1);
   const double close_past = iClose(InpTargetSymbol, PERIOD_H4, 25);
   if(close_now <= 0.0 || close_past <= 0.0)
      return false;
   double path = 0.0;
   for(int shift = 1; shift <= 24; shift++)
     {
      const double current_close = iClose(InpTargetSymbol, PERIOD_H4, shift);
      const double previous_close = iClose(InpTargetSymbol, PERIOD_H4, shift + 1);
      if(current_close <= 0.0 || previous_close <= 0.0)
         return false;
      path += MathAbs(current_close - previous_close);
     }
   if(path <= 0.0)
      return false;
   const double efficiency = MathAbs(close_now - close_past) / path;
   const double slope_atr = (ema_now - ema_past) / atr;

   double atr_history[];
   ArrayResize(atr_history, InpH4VolatilityBaseline);
   if(CopyBuffer(g_h4_atr_handle, 0, 2, InpH4VolatilityBaseline, atr_history) !=
      InpH4VolatilityBaseline)
      return false;
   ArraySort(atr_history);
   int percentile_index = (int)MathFloor(
      InpH4UnsafeAtrPercentile * (InpH4VolatilityBaseline - 1)
   );
   percentile_index = MathMax(0, MathMin(InpH4VolatilityBaseline - 1, percentile_index));
   const double atr_p95 = atr_history[percentile_index];
   const double h4_open = iOpen(InpTargetSymbol, PERIOD_H4, 1);
   const double prior_close = iClose(InpTargetSymbol, PERIOD_H4, 2);
   if(h4_open <= 0.0 || prior_close <= 0.0)
      return false;
   const double gap_atr = MathAbs(h4_open - prior_close) / atr;
   const bool unsafe = atr >= atr_p95 || gap_atr >= InpH4UnsafeGapAtr;
   if(unsafe || adx < InpH4TrendAdxMinimum || efficiency < InpH4TrendEfficiencyMin)
      return false;
   return slope_atr >= InpH4TrendSlopeAtrMin ||
          slope_atr <= -InpH4TrendSlopeAtrMin;
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

void EvaluateCompletedM5Bar()
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
   if(!MQLInfoInteger(MQL_TESTER) && (InpShadowMode || !InpEnableDemoOrders))
     {
      LogOrder("SHADOW_SIGNAL", direction, "demo_orders_disabled", 0.0, bid, ask, spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_ALLOWED))
     {
      LogOrder("GUARD_BLOCK", direction, "terminal_or_account_trading_disabled", 0.0, bid, ask, spread_points, 0.0, 0.0, 0.0, 0, "", 0, 0, 0.0);
      return;
     }

   const double recent_low = RecentLow(1, 6);
   const double recent_high = RecentHigh(1, 6);
   double stop_distance = MathMax(InpStopAtrMultiple * atr, InpStopFloorPoints * _Point);
   double sl = 0.0;
   double tp = 0.0;
   double stop_points = 0.0;
   if(direction == "LONG")
     {
      sl = NormalizeDouble(MathMin(recent_low, ask - stop_distance), _Digits);
      stop_distance = ask - sl;
      stop_points = stop_distance / _Point;
      tp = NormalizeDouble(ask + InpRiskReward * stop_distance, _Digits);
     }
   else
     {
      sl = NormalizeDouble(MathMax(recent_high, bid + stop_distance), _Digits);
      stop_distance = sl - bid;
      stop_points = stop_distance / _Point;
      tp = NormalizeDouble(bid - InpRiskReward * stop_distance, _Digits);
     }
   if(InpStopCeilingPoints > 0 && stop_points > InpStopCeilingPoints)
     {
      LogOrder("GUARD_BLOCK", direction, "stop_ceiling_exceeded", 0.0, bid, ask, spread_points, sl, tp, stop_points, 0, "", 0, 0, 0.0);
      return;
     }
   double requested_lots = InpFixedLots;
   if(H4TrendRiskOverlayActive())
      requested_lots += InpH4TrendAdditionalLots;
   const double lots = NormalizeVolume(requested_lots);
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
      if(AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
        {
         LogStartup("INIT_FAILED_NOT_DEMO", "Only Strategy Tester or a demo account is allowed.");
         return INIT_FAILED;
        }
      if(InpExpectedServerMarker != "" &&
         StringFind(AccountInfoString(ACCOUNT_SERVER), InpExpectedServerMarker) < 0)
        {
         LogStartup("INIT_FAILED_SERVER", "Demo server marker mismatch.");
         return INIT_FAILED;
        }
      if(InpAllowedAccountLogin > 0 &&
         AccountInfoInteger(ACCOUNT_LOGIN) != InpAllowedAccountLogin)
        {
         LogStartup("INIT_FAILED_LOGIN", "Account login is not allow-listed.");
         return INIT_FAILED;
        }
      if(!InpShadowMode && !InpEnableDemoOrders)
        {
         LogStartup("INIT_FAILED_ORDER_SWITCH", "Non-shadow mode requires explicit demo-order enablement.");
         return INIT_FAILED;
        }
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
   if(InpUseH4TrendRiskOverlay)
     {
      g_h4_atr_handle = iATR(InpTargetSymbol, PERIOD_H4, 14);
      g_h4_adx_handle = iADX(InpTargetSymbol, PERIOD_H4, 14);
      g_h4_ema_handle = iMA(InpTargetSymbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);
     }
   if(g_atr_handle == INVALID_HANDLE || g_bands_handle == INVALID_HANDLE || g_rsi_handle == INVALID_HANDLE)
     {
      LogStartup("INIT_FAILED_INDICATOR_HANDLE", "atr_bands_or_rsi_invalid");
      return INIT_FAILED;
     }
   if(InpUseH4TrendRiskOverlay &&
      (g_h4_atr_handle == INVALID_HANDLE ||
       g_h4_adx_handle == INVALID_HANDLE ||
       g_h4_ema_handle == INVALID_HANDLE))
     {
      LogStartup("INIT_FAILED_H4_OVERLAY_HANDLE", "h4_atr_adx_or_ema_invalid");
      return INIT_FAILED;
     }
   g_trade.SetExpertMagicNumber(InpMagicNumber);
   g_trade.SetDeviationInPoints(InpDeviationPoints);
   LogStartup("INIT_OK", MQLInfoInteger(MQL_TESTER) ? "tester" : (InpShadowMode ? "shadow_demo" : "ordering_demo"));
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   if(g_atr_handle != INVALID_HANDLE)
      IndicatorRelease(g_atr_handle);
   if(g_bands_handle != INVALID_HANDLE)
      IndicatorRelease(g_bands_handle);
   if(g_rsi_handle != INVALID_HANDLE)
      IndicatorRelease(g_rsi_handle);
   if(g_h4_atr_handle != INVALID_HANDLE)
      IndicatorRelease(g_h4_atr_handle);
   if(g_h4_adx_handle != INVALID_HANDLE)
      IndicatorRelease(g_h4_adx_handle);
   if(g_h4_ema_handle != INVALID_HANDLE)
      IndicatorRelease(g_h4_ema_handle);
  }

void OnTick()
  {
   const datetime current_m5 = iTime(InpTargetSymbol, InpSignalTimeframe, 0);
   if(current_m5 == 0 || current_m5 == g_last_m5_bar)
      return;
   g_last_m5_bar = current_m5;
   EvaluateCompletedM5Bar();
  }
