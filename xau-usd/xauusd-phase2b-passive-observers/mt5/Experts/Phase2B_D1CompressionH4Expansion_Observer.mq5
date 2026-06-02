#property strict
#property version   "1.000"
#property description "Phase 2B passive observer for d1_compression_h4_expansion_v0."

#include "../Include/CandidateObserverCommon.mqh"
#include "../Include/CandidateCostProjection.mqh"
#include "../Include/CandidateCsvLogger.mqh"
#include "../Include/CandidateSessionClock.mqh"
#include "../Include/CandidateSafetyGuard.mqh"

input string InpRunId = "phase2b-d1-compression-h4-expansion-observer-v0";
input string InpCandidateVersion = "v0";
input string InpHypothesisHash = "DRAFT_HASH_PENDING";
input string InpTargetSymbol = "XAUUSD";
input bool InpAllowResearchSymbolOverride = false;
input bool InpDryRunOnly = true;
input string InpObserverLogFileName = "phase2b_d1_compression_h4_expansion_observer.csv";
input int InpTimerSeconds = 10;

CCandidateCsvLogger g_logger;
datetime g_last_h4_decision_bar = 0;

void EvaluateD1CompressionH4Expansion(CandidateObservation &observation)
{
   if(Bars(_Symbol, PERIOD_D1) < 280 || Bars(_Symbol, PERIOD_H4) < 60)
   {
      observation.candidate_state = "DATA_INSUFFICIENT";
      observation.block_reason = "insufficient_d1_or_h4_history";
      observation.notes = "requires D1 252-day ATR percentile and H4 decision context";
      return;
   }

   double point = observation.point_size;
   if(point <= 0.0)
   {
      observation.candidate_state = "INVALID_CONTEXT";
      observation.block_reason = "point_unavailable";
      return;
   }

   double d1_atr_percentile = CandidateAtrPercentile(_Symbol, PERIOD_D1, 14, 252, 1);
   double box_high = CandidateHighestHigh(_Symbol, PERIOD_D1, 5, 1);
   double box_low = CandidateLowestLow(_Symbol, PERIOD_D1, 5, 1);
   double d1_median_range = CandidateMedianRangePrice(_Symbol, PERIOD_D1, 20, 1);
   double range5_width = box_high - box_low;
   double range5_average = range5_width / 5.0;

   if(box_high <= 0.0 || box_low <= 0.0 || d1_median_range <= 0.0 || range5_width <= 0.0)
   {
      observation.candidate_state = "DATA_INSUFFICIENT";
      observation.block_reason = "d1_compression_values_unavailable";
      return;
   }

   if(d1_atr_percentile > 30.0 || range5_average > d1_median_range)
   {
      observation.candidate_state = "WAIT_CONTEXT";
      observation.block_reason = "d1_compression_not_active";
      observation.notes = "atr_percentile=" + DoubleToString(d1_atr_percentile, 2);
      return;
   }

   double h4_open = iOpen(_Symbol, PERIOD_H4, 1);
   double h4_high = iHigh(_Symbol, PERIOD_H4, 1);
   double h4_low = iLow(_Symbol, PERIOD_H4, 1);
   double h4_close = iClose(_Symbol, PERIOD_H4, 1);
   double h4_range = h4_high - h4_low;
   double h4_body = MathAbs(h4_close - h4_open);
   double h4_atr = CandidateAtrPrice(_Symbol, PERIOD_H4, 14, 1);

   if(h4_open <= 0.0 || h4_high <= 0.0 || h4_low <= 0.0 || h4_close <= 0.0 || h4_range <= 0.0 || h4_atr <= 0.0)
   {
      observation.candidate_state = "DATA_INSUFFICIENT";
      observation.block_reason = "h4_decision_values_unavailable";
      return;
   }

   if(h4_body / h4_range < 0.50)
   {
      observation.candidate_state = "WAIT_TRIGGER";
      observation.block_reason = "h4_body_below_threshold";
      return;
   }

   bool is_long = h4_close > box_high && h4_close > h4_open;
   bool is_short = h4_close < box_low && h4_close < h4_open;
   if(!is_long && !is_short)
   {
      observation.candidate_state = "WAIT_TRIGGER";
      observation.block_reason = "h4_close_not_outside_compression_box";
      return;
   }

   observation.would_signal = true;
   observation.candidate_state = "WOULD_SIGNAL";
   observation.signal_direction = is_long ? "LONG" : "SHORT";
   observation.theoretical_entry = h4_close;

   if(is_long)
   {
      double risk_price = MathMax(h4_close - box_low, h4_atr);
      observation.theoretical_sl = h4_close - risk_price;
      observation.theoretical_tp_1_5r = h4_close + 1.5 * risk_price;
      observation.theoretical_tp_2_0r = h4_close + 2.0 * risk_price;
      observation.stop_distance_points = risk_price / point;
   }
   else
   {
      double risk_price = MathMax(box_high - h4_close, h4_atr);
      observation.theoretical_sl = h4_close + risk_price;
      observation.theoretical_tp_1_5r = h4_close - 1.5 * risk_price;
      observation.theoretical_tp_2_0r = h4_close - 2.0 * risk_price;
      observation.stop_distance_points = risk_price / point;
   }
   observation.block_reason = "none";
   observation.notes = "d1_atr_percentile=" + DoubleToString(d1_atr_percentile, 2);
}

int OnInit()
{
   string block_reason = "";
   if(!CandidateStartupGuard(InpDryRunOnly, _Symbol, InpTargetSymbol, InpAllowResearchSymbolOverride, block_reason))
   {
      Print("Phase2B_D1CompressionH4Expansion_Observer startup refused: ", block_reason);
      return INIT_FAILED;
   }

   g_logger.Configure(InpObserverLogFileName);
   if(!g_logger.EnsureHeader())
      return INIT_FAILED;

   EventSetTimer(InpTimerSeconds);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
}

void OnTimer()
{
   datetime h4_decision_bar = iTime(_Symbol, PERIOD_H4, 1);
   if(h4_decision_bar <= 0 || h4_decision_bar == g_last_h4_decision_bar)
      return;
   g_last_h4_decision_bar = h4_decision_bar;

   CandidateObservation observation;
   CandidateResetObservation(observation);
   CandidateFillMarket(
      observation,
      InpRunId,
      "d1_compression_h4_expansion_v0",
      InpCandidateVersion,
      InpHypothesisHash,
      "D1/H4",
      "H4"
   );
   observation.session_label = CandidateSessionLabel(TimeGMT());
   CandidateApplyPassiveFlags(observation);
   EvaluateD1CompressionH4Expansion(observation);
   CandidateApplyCostProjection(observation);
   g_logger.WriteObservation(observation);
}
