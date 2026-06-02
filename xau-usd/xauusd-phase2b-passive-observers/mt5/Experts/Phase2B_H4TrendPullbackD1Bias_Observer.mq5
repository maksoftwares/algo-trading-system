#property strict
#property version   "1.000"
#property description "Phase 2B passive observer for h4_trend_pullback_d1_bias_v0."

#include "../Include/CandidateObserverCommon.mqh"
#include "../Include/CandidateCostProjection.mqh"
#include "../Include/CandidateCsvLogger.mqh"
#include "../Include/CandidateSessionClock.mqh"
#include "../Include/CandidateSafetyGuard.mqh"

input string InpRunId = "phase2b-h4-trend-pullback-d1-bias-observer-v0";
input string InpCandidateVersion = "v0";
input string InpHypothesisHash = "DRAFT_HASH_PENDING";
input string InpTargetSymbol = "XAUUSD";
input bool InpAllowResearchSymbolOverride = false;
input bool InpDryRunOnly = true;
input string InpObserverLogFileName = "phase2b_h4_trend_pullback_d1_bias_observer.csv";
input int InpTimerSeconds = 10;

CCandidateCsvLogger g_logger;
datetime g_last_h4_decision_bar = 0;

void EvaluateH4TrendPullbackD1Bias(CandidateObservation &observation)
{
   if(Bars(_Symbol, PERIOD_D1) < 230 || Bars(_Symbol, PERIOD_H4) < 80)
   {
      observation.candidate_state = "DATA_INSUFFICIENT";
      observation.block_reason = "insufficient_d1_or_h4_history";
      return;
   }

   double point = observation.point_size;
   if(point <= 0.0)
   {
      observation.candidate_state = "INVALID_CONTEXT";
      observation.block_reason = "point_unavailable";
      return;
   }

   double d1_ema50 = CandidateEmaClose(_Symbol, PERIOD_D1, 50, 1);
   double d1_ema200 = CandidateEmaClose(_Symbol, PERIOD_D1, 200, 1);
   double d1_ema50_prior = CandidateEmaClose(_Symbol, PERIOD_D1, 50, 21);
   double h4_ema21 = CandidateEmaClose(_Symbol, PERIOD_H4, 21, 1);
   double h4_ema50 = CandidateEmaClose(_Symbol, PERIOD_H4, 50, 1);
   double h4_atr = CandidateAtrPrice(_Symbol, PERIOD_H4, 14, 1);

   if(d1_ema50 <= 0.0 || d1_ema200 <= 0.0 || d1_ema50_prior <= 0.0 || h4_ema21 <= 0.0 || h4_ema50 <= 0.0 || h4_atr <= 0.0)
   {
      observation.candidate_state = "DATA_INSUFFICIENT";
      observation.block_reason = "ema_or_atr_unavailable";
      return;
   }

   bool long_bias = d1_ema50 > d1_ema200 && d1_ema50 > d1_ema50_prior;
   bool short_bias = d1_ema50 < d1_ema200 && d1_ema50 < d1_ema50_prior;
   if(!long_bias && !short_bias)
   {
      observation.candidate_state = "WAIT_CONTEXT";
      observation.block_reason = "d1_trend_bias_not_active";
      return;
   }

   double h4_open = iOpen(_Symbol, PERIOD_H4, 1);
   double h4_high = iHigh(_Symbol, PERIOD_H4, 1);
   double h4_low = iLow(_Symbol, PERIOD_H4, 1);
   double h4_close = iClose(_Symbol, PERIOD_H4, 1);
   double h4_range = h4_high - h4_low;
   if(h4_open <= 0.0 || h4_high <= 0.0 || h4_low <= 0.0 || h4_close <= 0.0 || h4_range <= 0.0)
   {
      observation.candidate_state = "DATA_INSUFFICIENT";
      observation.block_reason = "h4_decision_values_unavailable";
      return;
   }

   double pullback_reference = long_bias ? h4_low : h4_high;
   double distance_to_ema21 = MathAbs(pullback_reference - h4_ema21);
   double distance_to_ema50 = MathAbs(pullback_reference - h4_ema50);
   bool pullback_near_average = MathMin(distance_to_ema21, distance_to_ema50) <= 0.5 * h4_atr;
   bool trend_structure_ok = long_bias ? h4_close > d1_ema200 : h4_close < d1_ema200;
   if(!pullback_near_average || !trend_structure_ok)
   {
      observation.candidate_state = "WAIT_TRIGGER";
      observation.block_reason = "h4_pullback_not_qualified";
      return;
   }

   double close_position = CandidateClosePosition(h4_high, h4_low, h4_close);
   bool long_confirmation = long_bias && h4_close > h4_open && close_position >= 0.65;
   bool short_confirmation = short_bias && h4_close < h4_open && close_position <= 0.35;
   if(!long_confirmation && !short_confirmation)
   {
      observation.candidate_state = "WAIT_TRIGGER";
      observation.block_reason = "h4_rejection_confirmation_missing";
      return;
   }

   bool is_long = long_confirmation;
   observation.would_signal = true;
   observation.candidate_state = "WOULD_SIGNAL";
   observation.signal_direction = is_long ? "LONG" : "SHORT";
   observation.theoretical_entry = h4_close;

   if(is_long)
   {
      double swing_low = CandidateLowestLow(_Symbol, PERIOD_H4, 5, 1);
      observation.theoretical_sl = swing_low - 0.25 * h4_atr;
      double risk_price = h4_close - observation.theoretical_sl;
      observation.theoretical_tp_1_5r = h4_close + 1.5 * risk_price;
      observation.theoretical_tp_2_0r = h4_close + 2.0 * risk_price;
      observation.stop_distance_points = risk_price / point;
   }
   else
   {
      double swing_high = CandidateHighestHigh(_Symbol, PERIOD_H4, 5, 1);
      observation.theoretical_sl = swing_high + 0.25 * h4_atr;
      double risk_price = observation.theoretical_sl - h4_close;
      observation.theoretical_tp_1_5r = h4_close - 1.5 * risk_price;
      observation.theoretical_tp_2_0r = h4_close - 2.0 * risk_price;
      observation.stop_distance_points = risk_price / point;
   }

   if(observation.stop_distance_points <= 0.0)
   {
      observation.candidate_state = "INVALID_CONTEXT";
      observation.would_signal = false;
      observation.signal_direction = "NONE";
      observation.block_reason = "invalid_stop_projection";
      return;
   }

   observation.block_reason = "none";
   observation.notes = "d1_ema50_slope_points=" + DoubleToString((d1_ema50 - d1_ema50_prior) / point, 2);
}

int OnInit()
{
   string block_reason = "";
   if(!CandidateStartupGuard(InpDryRunOnly, _Symbol, InpTargetSymbol, InpAllowResearchSymbolOverride, block_reason))
   {
      Print("Phase2B_H4TrendPullbackD1Bias_Observer startup refused: ", block_reason);
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
      "h4_trend_pullback_d1_bias_v0",
      InpCandidateVersion,
      InpHypothesisHash,
      "D1/H4",
      "H4"
   );
   observation.session_label = CandidateSessionLabel(TimeGMT());
   CandidateApplyPassiveFlags(observation);
   EvaluateH4TrendPullbackD1Bias(observation);
   CandidateApplyCostProjection(observation);
   g_logger.WriteObservation(observation);
}
