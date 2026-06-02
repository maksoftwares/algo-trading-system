#ifndef CANDIDATE_OBSERVER_COMMON_MQH
#define CANDIDATE_OBSERVER_COMMON_MQH

struct CandidateObservation
{
   string timestamp_utc;
   string timestamp_broker;
   string timestamp_local;
   string run_id;
   string candidate_id;
   string candidate_version;
   string hypothesis_hash;
   string symbol;
   string timeframe_decision;
   string timeframe_entry;
   double bid;
   double ask;
   double spread_points;
   double point_size;
   int digits;
   string session_label;
   string news_state_if_available;
   string candidate_state;
   bool would_signal;
   string signal_direction;
   double theoretical_entry;
   double theoretical_sl;
   double theoretical_tp_1_5r;
   double theoretical_tp_2_0r;
   double stop_distance_points;
   double measured_median_spread_points;
   double measured_p95_spread_points;
   double projected_cost_r_median;
   double projected_cost_r_p95;
   double projected_net_r_floor_assumption;
   bool cost_feasible;
   bool same_family_as_breakout_retest;
   bool dry_run;
   bool trade_permission;
   bool broker_action_allowed;
   bool phase2_execution_authorized;
   string block_reason;
   string notes;
};

string CandidateBoolText(const bool value)
{
   return value ? "true" : "false";
}

void CandidateResetObservation(CandidateObservation &observation)
{
   observation.timestamp_utc = "";
   observation.timestamp_broker = "";
   observation.timestamp_local = "";
   observation.run_id = "";
   observation.candidate_id = "";
   observation.candidate_version = "";
   observation.hypothesis_hash = "";
   observation.symbol = "";
   observation.timeframe_decision = "";
   observation.timeframe_entry = "";
   observation.bid = 0.0;
   observation.ask = 0.0;
   observation.spread_points = 0.0;
   observation.point_size = 0.0;
   observation.digits = 0;
   observation.session_label = "UNKNOWN";
   observation.news_state_if_available = "not_available";
   observation.candidate_state = "WAIT_CONTEXT";
   observation.would_signal = false;
   observation.signal_direction = "NONE";
   observation.theoretical_entry = 0.0;
   observation.theoretical_sl = 0.0;
   observation.theoretical_tp_1_5r = 0.0;
   observation.theoretical_tp_2_0r = 0.0;
   observation.stop_distance_points = 0.0;
   observation.measured_median_spread_points = 50.0;
   observation.measured_p95_spread_points = 75.0;
   observation.projected_cost_r_median = 0.0;
   observation.projected_cost_r_p95 = 0.0;
   observation.projected_net_r_floor_assumption = -999.0;
   observation.cost_feasible = false;
   observation.same_family_as_breakout_retest = false;
   observation.dry_run = true;
   observation.trade_permission = false;
   observation.broker_action_allowed = false;
   observation.phase2_execution_authorized = false;
   observation.block_reason = "not_evaluated";
   observation.notes = "";
}

void CandidateFillMarket(
   CandidateObservation &observation,
   const string run_id,
   const string candidate_id,
   const string candidate_version,
   const string hypothesis_hash,
   const string timeframe_decision,
   const string timeframe_entry
)
{
   observation.timestamp_broker = TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS);
   observation.timestamp_utc = TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS);
   observation.timestamp_local = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   observation.run_id = run_id;
   observation.candidate_id = candidate_id;
   observation.candidate_version = candidate_version;
   observation.hypothesis_hash = hypothesis_hash;
   observation.symbol = _Symbol;
   observation.timeframe_decision = timeframe_decision;
   observation.timeframe_entry = timeframe_entry;
   observation.bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   observation.ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   observation.point_size = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   observation.digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   observation.spread_points = observation.point_size > 0.0 ? (observation.ask - observation.bid) / observation.point_size : 0.0;
}

double CandidateTrueRangePrice(const string symbol_name, const ENUM_TIMEFRAMES timeframe, const int shift)
{
   double high_price = iHigh(symbol_name, timeframe, shift);
   double low_price = iLow(symbol_name, timeframe, shift);
   double previous_close = iClose(symbol_name, timeframe, shift + 1);
   if(high_price <= 0.0 || low_price <= 0.0 || previous_close <= 0.0 || high_price < low_price)
      return 0.0;
   double range_a = high_price - low_price;
   double range_b = MathAbs(high_price - previous_close);
   double range_c = MathAbs(low_price - previous_close);
   return MathMax(range_a, MathMax(range_b, range_c));
}

double CandidateAtrPrice(
   const string symbol_name,
   const ENUM_TIMEFRAMES timeframe,
   const int period,
   const int start_shift
)
{
   double total = 0.0;
   int counted = 0;
   for(int shift = start_shift; shift < start_shift + period; shift++)
   {
      double value = CandidateTrueRangePrice(symbol_name, timeframe, shift);
      if(value <= 0.0)
         continue;
      total += value;
      counted++;
   }
   if(counted <= 0)
      return 0.0;
   return total / counted;
}

double CandidateAtrPoints(
   const string symbol_name,
   const ENUM_TIMEFRAMES timeframe,
   const int period,
   const int start_shift
)
{
   double point = SymbolInfoDouble(symbol_name, SYMBOL_POINT);
   double atr_price = CandidateAtrPrice(symbol_name, timeframe, period, start_shift);
   if(point <= 0.0)
      return 0.0;
   return atr_price / point;
}

double CandidateHighestHigh(
   const string symbol_name,
   const ENUM_TIMEFRAMES timeframe,
   const int lookback,
   const int start_shift
)
{
   double result = 0.0;
   for(int shift = start_shift; shift < start_shift + lookback; shift++)
   {
      double value = iHigh(symbol_name, timeframe, shift);
      if(value <= 0.0)
         continue;
      if(result <= 0.0 || value > result)
         result = value;
   }
   return result;
}

double CandidateLowestLow(
   const string symbol_name,
   const ENUM_TIMEFRAMES timeframe,
   const int lookback,
   const int start_shift
)
{
   double result = 0.0;
   for(int shift = start_shift; shift < start_shift + lookback; shift++)
   {
      double value = iLow(symbol_name, timeframe, shift);
      if(value <= 0.0)
         continue;
      if(result <= 0.0 || value < result)
         result = value;
   }
   return result;
}

double CandidateMedianRangePrice(
   const string symbol_name,
   const ENUM_TIMEFRAMES timeframe,
   const int lookback,
   const int start_shift
)
{
   double values[];
   ArrayResize(values, lookback);
   int count = 0;
   for(int shift = start_shift; shift < start_shift + lookback; shift++)
   {
      double high_price = iHigh(symbol_name, timeframe, shift);
      double low_price = iLow(symbol_name, timeframe, shift);
      if(high_price <= 0.0 || low_price <= 0.0 || high_price < low_price)
         continue;
      values[count] = high_price - low_price;
      count++;
   }
   if(count <= 0)
      return 0.0;
   ArrayResize(values, count);
   ArraySort(values);
   int middle = count / 2;
   if(count % 2 == 1)
      return values[middle];
   return 0.5 * (values[middle - 1] + values[middle]);
}

double CandidateAtrPercentile(
   const string symbol_name,
   const ENUM_TIMEFRAMES timeframe,
   const int atr_period,
   const int lookback,
   const int start_shift
)
{
   double current = CandidateAtrPrice(symbol_name, timeframe, atr_period, start_shift);
   if(current <= 0.0)
      return 100.0;
   int total = 0;
   int at_or_below = 0;
   for(int shift = start_shift; shift < start_shift + lookback; shift++)
   {
      double value = CandidateAtrPrice(symbol_name, timeframe, atr_period, shift);
      if(value <= 0.0)
         continue;
      total++;
      if(value <= current)
         at_or_below++;
   }
   if(total <= 0)
      return 100.0;
   return 100.0 * ((double)at_or_below / (double)total);
}

double CandidateEmaClose(
   const string symbol_name,
   const ENUM_TIMEFRAMES timeframe,
   const int period,
   const int shift
)
{
   int history = period * 4;
   if(Bars(symbol_name, timeframe) < shift + history + 2)
      return 0.0;
   double alpha = 2.0 / ((double)period + 1.0);
   double ema = iClose(symbol_name, timeframe, shift + history);
   if(ema <= 0.0)
      return 0.0;
   for(int index = shift + history - 1; index >= shift; index--)
   {
      double close_price = iClose(symbol_name, timeframe, index);
      if(close_price <= 0.0)
         return 0.0;
      ema = alpha * close_price + (1.0 - alpha) * ema;
   }
   return ema;
}

double CandidateClosePosition(const double high_price, const double low_price, const double close_price)
{
   double range = high_price - low_price;
   if(range <= 0.0)
      return 0.5;
   return (close_price - low_price) / range;
}

#endif
