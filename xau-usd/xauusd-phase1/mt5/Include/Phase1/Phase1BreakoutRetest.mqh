#ifndef PHASE1_BREAKOUT_RETEST_MQH
#define PHASE1_BREAKOUT_RETEST_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1BreakoutRetestObserver
{
private:
   int m_break_window_bars;
   double m_break_atr_multiplier;
   double m_retest_tolerance_points;
   double m_stop_atr_multiplier;
   double m_reward_multiple;
   bool m_swing_only;

public:
   void Configure(const bool swing_only)
   {
      m_break_window_bars = 20;
      m_break_atr_multiplier = 0.30;
      m_retest_tolerance_points = 5.0;
      m_stop_atr_multiplier = 0.10;
      m_reward_multiple = 1.50;
      m_swing_only = swing_only;
   }

   bool Evaluate(
      const string symbol_name,
      const double point,
      Phase1BreakoutRetestObservation &observation
   ) const
   {
      Phase1ResetBreakoutRetestObservation(observation);
      if(point <= 0.0)
      {
         observation.stage = "NO_POINT";
         observation.reason_code = "point_unavailable";
         return false;
      }

      if(Bars(symbol_name, PERIOD_M5) < 80)
      {
         observation.stage = "INSUFFICIENT_BARS";
         observation.reason_code = "insufficient_m5_history";
         return false;
      }

      double confirmation_open = iOpen(symbol_name, PERIOD_M5, 1);
      double confirmation_close = iClose(symbol_name, PERIOD_M5, 1);
      if(confirmation_open <= 0.0 || confirmation_close <= 0.0)
      {
         observation.stage = "NO_CONFIRMATION_BAR";
         observation.reason_code = "confirmation_bar_unavailable";
         return false;
      }

      if(confirmation_close > confirmation_open)
         return EvaluateDirection(symbol_name, point, true, observation);
      if(confirmation_close < confirmation_open)
         return EvaluateDirection(symbol_name, point, false, observation);

      observation.stage = "WAIT_CONFIRMATION";
      observation.reason_code = "confirmation_candle_neutral";
      return false;
   }

private:
   bool EvaluateDirection(
      const string symbol_name,
      const double point,
      const bool is_long,
      Phase1BreakoutRetestObservation &observation
   ) const
   {
      observation.direction_text = is_long ? "LONG" : "SHORT";
      observation.confirmation_valid = true;
      observation.stage = "CONFIRMATION_DETECTED";

      double retest_high = iHigh(symbol_name, PERIOD_M5, 2);
      double retest_low = iLow(symbol_name, PERIOD_M5, 2);
      double retest_close = iClose(symbol_name, PERIOD_M5, 2);
      double retest_atr = AverageRangePrice(symbol_name, PERIOD_M5, 14, 2);
      if(retest_high <= 0.0 || retest_low <= 0.0 || retest_close <= 0.0 || retest_atr <= 0.0)
      {
         observation.stage = "WAIT_RETEST";
         observation.reason_code = "retest_context_unavailable";
         return false;
      }

      Candidate best;
      ResetCandidate(best);
      for(int shift = 3; shift <= 2 + m_break_window_bars; shift++)
      {
         double break_atr = AverageRangePrice(symbol_name, PERIOD_M5, 14, shift);
         double break_close = iClose(symbol_name, PERIOD_M5, shift);
         if(break_atr <= 0.0 || break_close <= 0.0)
            continue;

         Candidate levels[3];
         int count = CandidateLevels(symbol_name, point, is_long, shift, levels);
         for(int index = 0; index < count; index++)
         {
            Candidate candidate = levels[index];
            candidate.break_shift = shift;
            if(!BreakValid(break_close, break_atr, candidate.level_price, is_long))
               continue;
            if(!RetestValid(retest_high, retest_low, retest_close, candidate.level_price, point, is_long))
               continue;

            BuildPlan(retest_high, retest_low, retest_atr, point, is_long, candidate);
            if(candidate.stop_distance_points <= 0.0)
               continue;
            if(!best.valid || candidate.stop_distance_points < best.stop_distance_points)
               best = candidate;
         }
      }

      observation.level_found = best.valid;
      if(!best.valid)
      {
         observation.stage = "WAIT_LEVEL_BREAK_RETEST";
         if(m_swing_only)
            observation.reason_code = is_long ? "no_long_swing_breakout_retest_candidate" : "no_short_swing_breakout_retest_candidate";
         else
            observation.reason_code = is_long ? "no_long_breakout_retest_candidate" : "no_short_breakout_retest_candidate";
         return false;
      }

      observation.break_found = true;
      observation.retest_valid = true;
      observation.stage = "WOULD_SIGNAL";
      if(m_swing_only)
         observation.reason_code = is_long ? "SWING_BREAKOUT_RETEST_LONG_DRY_RUN" : "SWING_BREAKOUT_RETEST_SHORT_DRY_RUN";
      else
         observation.reason_code = is_long ? "BREAKOUT_RETEST_LONG_DRY_RUN" : "BREAKOUT_RETEST_SHORT_DRY_RUN";
      observation.would_signal = true;
      observation.level_kind = best.level_kind;
      observation.level_price = best.level_price;
      observation.entry_price = best.entry_price;
      observation.stop_loss = best.stop_loss;
      observation.take_profit = best.take_profit;
      observation.stop_distance_points = best.stop_distance_points;
      observation.break_shift = best.break_shift;
      return true;
   }

   struct Candidate
   {
      bool valid;
      string level_kind;
      double level_price;
      double entry_price;
      double stop_loss;
      double take_profit;
      double stop_distance_points;
      int break_shift;
   };

   void ResetCandidate(Candidate &candidate) const
   {
      candidate.valid = false;
      candidate.level_kind = "none";
      candidate.level_price = 0.0;
      candidate.entry_price = 0.0;
      candidate.stop_loss = 0.0;
      candidate.take_profit = 0.0;
      candidate.stop_distance_points = 0.0;
      candidate.break_shift = -1;
   }

   int CandidateLevels(
      const string symbol_name,
      const double point,
      const bool is_long,
      const int break_shift,
      Candidate &levels[]
   ) const
   {
      int count = 0;
      if(m_swing_only)
      {
         AddLevel(levels, count, is_long ? "latest_swing_high" : "latest_swing_low", SwingLevel(symbol_name, is_long, break_shift), point);
         return count;
      }
      AddLevel(levels, count, is_long ? "previous_daily_high" : "previous_daily_low", DailyLevel(symbol_name, is_long), point);
      AddLevel(levels, count, is_long ? "previous_weekly_high" : "previous_weekly_low", WeeklyLevel(symbol_name, is_long), point);
      AddLevel(levels, count, is_long ? "latest_swing_high" : "latest_swing_low", SwingLevel(symbol_name, is_long, break_shift), point);
      return count;
   }

   void AddLevel(Candidate &levels[], int &count, const string kind, const double price, const double point) const
   {
      if(price <= 0.0 || point <= 0.0 || count >= 3)
         return;
      for(int index = 0; index < count; index++)
      {
         if(MathAbs(levels[index].level_price - price) <= 10.0 * point)
            return;
      }
      ResetCandidate(levels[count]);
      levels[count].valid = true;
      levels[count].level_kind = kind;
      levels[count].level_price = price;
      count++;
   }

   double DailyLevel(const string symbol_name, const bool is_long) const
   {
      return is_long ? iHigh(symbol_name, PERIOD_D1, 1) : iLow(symbol_name, PERIOD_D1, 1);
   }

   double WeeklyLevel(const string symbol_name, const bool is_long) const
   {
      return is_long ? iHigh(symbol_name, PERIOD_W1, 1) : iLow(symbol_name, PERIOD_W1, 1);
   }

   double SwingLevel(const string symbol_name, const bool is_long, const int start_shift) const
   {
      for(int shift = MathMax(start_shift, 6); shift < start_shift + 80; shift++)
      {
         double price = is_long ? iHigh(symbol_name, PERIOD_M5, shift) : iLow(symbol_name, PERIOD_M5, shift);
         if(price <= 0.0)
            continue;
         bool confirmed = true;
         for(int offset = 1; offset <= 4; offset++)
         {
            double newer = is_long ? iHigh(symbol_name, PERIOD_M5, shift - offset) : iLow(symbol_name, PERIOD_M5, shift - offset);
            double older = is_long ? iHigh(symbol_name, PERIOD_M5, shift + offset) : iLow(symbol_name, PERIOD_M5, shift + offset);
            if(newer <= 0.0 || older <= 0.0)
            {
               confirmed = false;
               break;
            }
            if(is_long && (price <= newer || price <= older))
               confirmed = false;
            if(!is_long && (price >= newer || price >= older))
               confirmed = false;
         }
         if(confirmed)
            return price;
      }
      return 0.0;
   }

   bool BreakValid(
      const double break_close,
      const double break_atr,
      const double level_price,
      const bool is_long
   ) const
   {
      if(is_long)
         return break_close >= level_price + m_break_atr_multiplier * break_atr;
      return break_close <= level_price - m_break_atr_multiplier * break_atr;
   }

   bool RetestValid(
      const double retest_high,
      const double retest_low,
      const double retest_close,
      const double level_price,
      const double point,
      const bool is_long
   ) const
   {
      if(is_long)
         return retest_low <= level_price + m_retest_tolerance_points * point && retest_close >= level_price;
      return retest_high >= level_price - m_retest_tolerance_points * point && retest_close <= level_price;
   }

   void BuildPlan(
      const double retest_high,
      const double retest_low,
      const double retest_atr,
      const double point,
      const bool is_long,
      Candidate &candidate
   ) const
   {
      if(is_long)
      {
         candidate.entry_price = retest_high + point;
         candidate.stop_loss = retest_low - m_stop_atr_multiplier * retest_atr;
         double risk_price = candidate.entry_price - candidate.stop_loss;
         candidate.take_profit = candidate.entry_price + m_reward_multiple * risk_price;
         candidate.stop_distance_points = risk_price / point;
      }
      else
      {
         candidate.entry_price = retest_low - point;
         candidate.stop_loss = retest_high + m_stop_atr_multiplier * retest_atr;
         double risk_price = candidate.stop_loss - candidate.entry_price;
         candidate.take_profit = candidate.entry_price - m_reward_multiple * risk_price;
         candidate.stop_distance_points = risk_price / point;
      }
   }

   double AverageRangePrice(
      const string symbol_name,
      const ENUM_TIMEFRAMES timeframe,
      const int periods,
      const int start_shift
   ) const
   {
      double total = 0.0;
      int counted = 0;
      for(int shift = start_shift; shift < start_shift + periods; shift++)
      {
         double high_price = iHigh(symbol_name, timeframe, shift);
         double low_price = iLow(symbol_name, timeframe, shift);
         if(high_price <= 0.0 || low_price <= 0.0 || high_price < low_price)
            continue;
         total += high_price - low_price;
         counted++;
      }
      if(counted <= 0)
         return 0.0;
      return total / counted;
   }
};

#endif
