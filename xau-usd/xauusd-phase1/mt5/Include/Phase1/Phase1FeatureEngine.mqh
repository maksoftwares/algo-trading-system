#ifndef PHASE1_FEATURE_ENGINE_MQH
#define PHASE1_FEATURE_ENGINE_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1FeatureEngine
{
public:
   bool Build(const string symbol_name, const double point, Phase1FeatureSnapshot &features) const
   {
      Phase1ResetFeatureSnapshot(features);
      if(point <= 0.0)
         return false;

      features.m5_range_points = CandleRangePoints(symbol_name, PERIOD_M5, 1, point);
      features.m15_range_points = CandleRangePoints(symbol_name, PERIOD_M15, 1, point);
      features.h1_range_points = CandleRangePoints(symbol_name, PERIOD_H1, 1, point);
      features.atr14_points = AverageRangePoints(symbol_name, PERIOD_M5, 14, point);

      double open_price = iOpen(symbol_name, PERIOD_M5, 1);
      double high_price = iHigh(symbol_name, PERIOD_M5, 1);
      double low_price = iLow(symbol_name, PERIOD_M5, 1);
      double close_price = iClose(symbol_name, PERIOD_M5, 1);
      if(high_price <= 0.0 || low_price <= 0.0)
         return false;

      features.m5_body_points = MathAbs(close_price - open_price) / point;
      features.m5_upper_wick_points = (high_price - MathMax(open_price, close_price)) / point;
      features.m5_lower_wick_points = (MathMin(open_price, close_price) - low_price) / point;
      features.compression_state = (
         features.atr14_points > 0.0 &&
         features.m5_range_points > 0.0 &&
         features.m5_range_points < (0.50 * features.atr14_points)
      );
      features.feature_ok = true;
      return true;
   }

private:
   double CandleRangePoints(
      const string symbol_name,
      const ENUM_TIMEFRAMES timeframe,
      const int shift,
      const double point
   ) const
   {
      double high_price = iHigh(symbol_name, timeframe, shift);
      double low_price = iLow(symbol_name, timeframe, shift);
      if(high_price <= 0.0 || low_price <= 0.0 || high_price < low_price || point <= 0.0)
         return 0.0;
      return (high_price - low_price) / point;
   }

   double AverageRangePoints(
      const string symbol_name,
      const ENUM_TIMEFRAMES timeframe,
      const int periods,
      const double point
   ) const
   {
      if(periods <= 0 || point <= 0.0)
         return 0.0;

      double total = 0.0;
      int counted = 0;
      for(int shift = 1; shift <= periods; shift++)
      {
         double range_points = CandleRangePoints(symbol_name, timeframe, shift, point);
         if(range_points <= 0.0)
            continue;
         total += range_points;
         counted++;
      }

      if(counted <= 0)
         return 0.0;
      return total / counted;
   }
};

#endif
