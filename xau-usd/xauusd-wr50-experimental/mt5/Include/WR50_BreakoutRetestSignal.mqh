#ifndef WR50_BREAKOUT_RETEST_SIGNAL_MQH
#define WR50_BREAKOUT_RETEST_SIGNAL_MQH

#include "WR50_SessionFilter.mqh"
#include "WR50_SpreadGuard.mqh"
#include "WR50_Types.mqh"

double WR50_GetAtrPoints(const string symbol, const int period, const int shift)
{
   int handle = iATR(symbol, PERIOD_M5, period);
   if(handle == INVALID_HANDLE)
      return 0.0;
   double atr[];
   ArraySetAsSeries(atr, true);
   if(CopyBuffer(handle, 0, 0, shift + 5, atr) <= shift)
   {
      IndicatorRelease(handle);
      return 0.0;
   }
   IndicatorRelease(handle);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   if(point <= 0.0)
      return 0.0;
   return atr[shift] / point;
}

bool WR50_IsSwingHigh(MqlRates &rates[], const int shift, const int left, const int right)
{
   for(int i = 1; i <= left; i++)
      if(rates[shift].high <= rates[shift + i].high)
         return false;
   for(int j = 1; j <= right; j++)
      if(rates[shift].high <= rates[shift - j].high)
         return false;
   return true;
}

bool WR50_IsSwingLow(MqlRates &rates[], const int shift, const int left, const int right)
{
   for(int i = 1; i <= left; i++)
      if(rates[shift].low >= rates[shift + i].low)
         return false;
   for(int j = 1; j <= right; j++)
      if(rates[shift].low >= rates[shift - j].low)
         return false;
   return true;
}

bool WR50_FindLatestSwing(MqlRates &rates[],
                          const int count,
                          const bool high,
                          const int left,
                          const int right,
                          double &level)
{
   for(int shift = right + 1; shift < count - left; shift++)
   {
      if(high && WR50_IsSwingHigh(rates, shift, left, right))
      {
         level = rates[shift].high;
         return true;
      }
      if(!high && WR50_IsSwingLow(rates, shift, left, right))
      {
         level = rates[shift].low;
         return true;
      }
   }
   return false;
}

bool WR50_QualityCandlePasses(const MqlRates &bar,
                              const int direction,
                              const double min_body_to_range,
                              const double max_opposing_wick_to_range)
{
   double range = bar.high - bar.low;
   if(range <= 0.0)
      return false;
   double body = MathAbs(bar.close - bar.open);
   double body_ratio = body / range;
   if(body_ratio < min_body_to_range)
      return false;
   double opposing_wick = 0.0;
   if(direction == WR50_DIRECTION_LONG)
      opposing_wick = MathMin(bar.open, bar.close) - bar.low;
   else
      opposing_wick = bar.high - MathMax(bar.open, bar.close);
   return (opposing_wick / range) <= max_opposing_wick_to_range;
}

bool WR50_CheckLongRetest(MqlRates &rates[],
                          const int count,
                          const double level,
                          const double break_threshold_price,
                          const double retest_proximity_price,
                          const double sl_offset_price,
                          const double tp_r,
                          const bool require_quality,
                          const double min_body_to_range,
                          const double max_opposing_wick_to_range,
                          const string reason_code,
                          WR50Signal &signal)
{
   if(count < 25)
      return false;
   bool broke = false;
   for(int shift = 3; shift <= 22 && shift < count; shift++)
   {
      if(rates[shift].close > level + break_threshold_price)
      {
         broke = true;
         break;
      }
   }
   if(!broke)
      return false;
   if(!(rates[2].low <= level + retest_proximity_price && rates[2].close >= level))
      return false;
   if(!(rates[1].close > rates[1].open))
      return false;
   if(require_quality && !WR50_QualityCandlePasses(rates[1], WR50_DIRECTION_LONG, min_body_to_range, max_opposing_wick_to_range))
      return false;

   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   signal.has_signal = true;
   signal.direction = WR50_DIRECTION_LONG;
   signal.entry_price = NormalizeDouble(rates[2].high + point, _Digits);
   signal.sl_price = NormalizeDouble(rates[2].low - sl_offset_price, _Digits);
   double risk = signal.entry_price - signal.sl_price;
   signal.tp_price = NormalizeDouble(signal.entry_price + (risk * tp_r), _Digits);
   signal.entry_type = "BUY_STOP";
   signal.reason_code = reason_code;
   signal.session_bucket = WR50_SessionBucket();
   signal.entry_spread_points = WR50_CurrentSpreadPoints(_Symbol);
   return true;
}

bool WR50_CheckShortRetest(MqlRates &rates[],
                           const int count,
                           const double level,
                           const double break_threshold_price,
                           const double retest_proximity_price,
                           const double sl_offset_price,
                           const double tp_r,
                           const bool require_quality,
                           const double min_body_to_range,
                           const double max_opposing_wick_to_range,
                           const string reason_code,
                           WR50Signal &signal)
{
   if(count < 25)
      return false;
   bool broke = false;
   for(int shift = 3; shift <= 22 && shift < count; shift++)
   {
      if(rates[shift].close < level - break_threshold_price)
      {
         broke = true;
         break;
      }
   }
   if(!broke)
      return false;
   if(!(rates[2].high >= level - retest_proximity_price && rates[2].close <= level))
      return false;
   if(!(rates[1].close < rates[1].open))
      return false;
   if(require_quality && !WR50_QualityCandlePasses(rates[1], WR50_DIRECTION_SHORT, min_body_to_range, max_opposing_wick_to_range))
      return false;

   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   signal.has_signal = true;
   signal.direction = WR50_DIRECTION_SHORT;
   signal.entry_price = NormalizeDouble(rates[2].low - point, _Digits);
   signal.sl_price = NormalizeDouble(rates[2].high + sl_offset_price, _Digits);
   double risk = signal.sl_price - signal.entry_price;
   signal.tp_price = NormalizeDouble(signal.entry_price - (risk * tp_r), _Digits);
   signal.entry_type = "SELL_STOP";
   signal.reason_code = reason_code;
   signal.session_bucket = WR50_SessionBucket();
   signal.entry_spread_points = WR50_CurrentSpreadPoints(_Symbol);
   return true;
}

bool WR50_GetBreakoutRetestSignal(const string symbol,
                                  const double tp_r,
                                  const double break_atr_multiple,
                                  const bool require_quality,
                                  const double min_body_to_range,
                                  const double max_opposing_wick_to_range,
                                  const int retest_proximity_points,
                                  const double sl_atr_multiple,
                                  const string long_reason,
                                  const string short_reason,
                                  WR50Signal &signal)
{
   WR50_ResetSignal(signal);
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   int count = CopyRates(symbol, PERIOD_M5, 0, 80, rates);
   if(count < 50)
   {
      signal.block_reason = "not_enough_m5_bars";
      return false;
   }

   double atr_points = WR50_GetAtrPoints(symbol, 14, 1);
   if(atr_points <= 0.0)
   {
      signal.block_reason = "atr_unavailable";
      return false;
   }
   signal.atr_points = atr_points;

   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   double levels[6];
   int level_count = 0;
   levels[level_count++] = iHigh(symbol, PERIOD_D1, 1);
   levels[level_count++] = iLow(symbol, PERIOD_D1, 1);
   levels[level_count++] = iHigh(symbol, PERIOD_W1, 1);
   levels[level_count++] = iLow(symbol, PERIOD_W1, 1);
   double swing_high = 0.0;
   double swing_low = 0.0;
   if(WR50_FindLatestSwing(rates, count, true, 4, 4, swing_high))
      levels[level_count++] = swing_high;
   if(WR50_FindLatestSwing(rates, count, false, 4, 4, swing_low))
      levels[level_count++] = swing_low;

   double break_threshold_price = break_atr_multiple * atr_points * point;
   double retest_proximity_price = retest_proximity_points * point;
   double sl_offset_price = sl_atr_multiple * atr_points * point;

   for(int i = 0; i < level_count; i++)
   {
      if(levels[i] <= 0.0)
         continue;
      if(WR50_CheckLongRetest(rates, count, levels[i], break_threshold_price, retest_proximity_price,
                              sl_offset_price, tp_r, require_quality, min_body_to_range,
                              max_opposing_wick_to_range, long_reason, signal))
         return true;
      if(WR50_CheckShortRetest(rates, count, levels[i], break_threshold_price, retest_proximity_price,
                               sl_offset_price, tp_r, require_quality, min_body_to_range,
                               max_opposing_wick_to_range, short_reason, signal))
         return true;
   }

   signal.block_reason = "no_breakout_retest_signal";
   return false;
}

#endif

