#property strict
#property version   "1.000"
#property description "Phase 2B passive observer for weekly_level_h4_rejection_v0."

#include "../Include/CandidateObserverCommon.mqh"
#include "../Include/CandidateCostProjection.mqh"
#include "../Include/CandidateCsvLogger.mqh"
#include "../Include/CandidateSessionClock.mqh"
#include "../Include/CandidateSafetyGuard.mqh"

input string InpRunId = "phase2b-weekly-level-h4-rejection-observer-v0";
input string InpCandidateVersion = "v0";
input string InpHypothesisHash = "DRAFT_HASH_PENDING";
input string InpTargetSymbol = "XAUUSD";
input bool InpAllowResearchSymbolOverride = false;
input bool InpDryRunOnly = true;
input string InpObserverLogFileName = "phase2b_weekly_level_h4_rejection_observer.csv";
input int InpTimerSeconds = 10;

CCandidateCsvLogger g_logger;
datetime g_last_h4_decision_bar = 0;

bool TryWeeklyLevelRejection(
   CandidateObservation &observation,
   const double level_price,
   const bool resistance_level,
   const string level_name,
   const double h4_atr
)
{
   double point = observation.point_size;
   double h4_open = iOpen(_Symbol, PERIOD_H4, 1);
   double h4_high = iHigh(_Symbol, PERIOD_H4, 1);
   double h4_low = iLow(_Symbol, PERIOD_H4, 1);
   double h4_close = iClose(_Symbol, PERIOD_H4, 1);
   double body = MathAbs(h4_close - h4_open);
   if(body < point)
      body = point;
   double upper_wick = h4_high - MathMax(h4_open, h4_close);
   double lower_wick = MathMin(h4_open, h4_close) - h4_low;
   double zone = 0.25 * h4_atr;

   if(level_price <= 0.0 || h4_atr <= 0.0 || point <= 0.0)
      return false;

   if(resistance_level)
   {
      bool touched = h4_high >= level_price - zone && h4_low <= level_price + zone;
      bool rejected = upper_wick >= 1.5 * body && h4_close < level_price;
      if(!touched || !rejected)
         return false;
      observation.would_signal = true;
      observation.candidate_state = "WOULD_SIGNAL";
      observation.signal_direction = "SHORT";
      observation.theoretical_entry = h4_close;
      observation.theoretical_sl = h4_high + 0.25 * h4_atr;
      double risk_price = observation.theoretical_sl - h4_close;
      observation.theoretical_tp_1_5r = h4_close - 1.5 * risk_price;
      observation.theoretical_tp_2_0r = h4_close - 2.0 * risk_price;
      observation.stop_distance_points = risk_price / point;
      observation.block_reason = "none";
      observation.notes = "level=" + level_name;
      return observation.stop_distance_points > 0.0;
   }

   bool touched = h4_low <= level_price + zone && h4_high >= level_price - zone;
   bool rejected = lower_wick >= 1.5 * body && h4_close > level_price;
   if(!touched || !rejected)
      return false;
   observation.would_signal = true;
   observation.candidate_state = "WOULD_SIGNAL";
   observation.signal_direction = "LONG";
   observation.theoretical_entry = h4_close;
   observation.theoretical_sl = h4_low - 0.25 * h4_atr;
   double risk_price = h4_close - observation.theoretical_sl;
   observation.theoretical_tp_1_5r = h4_close + 1.5 * risk_price;
   observation.theoretical_tp_2_0r = h4_close + 2.0 * risk_price;
   observation.stop_distance_points = risk_price / point;
   observation.block_reason = "none";
   observation.notes = "level=" + level_name;
   return observation.stop_distance_points > 0.0;
}

void EvaluateWeeklyLevelH4Rejection(CandidateObservation &observation)
{
   if(Bars(_Symbol, PERIOD_W1) < 10 || Bars(_Symbol, PERIOD_H4) < 60)
   {
      observation.candidate_state = "DATA_INSUFFICIENT";
      observation.block_reason = "insufficient_w1_or_h4_history";
      return;
   }

   double h4_atr = CandidateAtrPrice(_Symbol, PERIOD_H4, 14, 1);
   if(h4_atr <= 0.0 || observation.point_size <= 0.0)
   {
      observation.candidate_state = "DATA_INSUFFICIENT";
      observation.block_reason = "h4_atr_unavailable";
      return;
   }

   double previous_week_high = iHigh(_Symbol, PERIOD_W1, 1);
   double previous_week_low = iLow(_Symbol, PERIOD_W1, 1);
   double four_week_high = CandidateHighestHigh(_Symbol, PERIOD_W1, 4, 1);
   double four_week_low = CandidateLowestLow(_Symbol, PERIOD_W1, 4, 1);

   if(TryWeeklyLevelRejection(observation, previous_week_high, true, "previous_week_high", h4_atr))
      return;
   if(TryWeeklyLevelRejection(observation, previous_week_low, false, "previous_week_low", h4_atr))
      return;
   if(TryWeeklyLevelRejection(observation, four_week_high, true, "prior_4_week_high", h4_atr))
      return;
   if(TryWeeklyLevelRejection(observation, four_week_low, false, "prior_4_week_low", h4_atr))
      return;

   observation.candidate_state = "WAIT_TRIGGER";
   observation.block_reason = "no_h4_weekly_level_rejection";
}

int OnInit()
{
   string block_reason = "";
   if(!CandidateStartupGuard(InpDryRunOnly, _Symbol, InpTargetSymbol, InpAllowResearchSymbolOverride, block_reason))
   {
      Print("Phase2B_WeeklyLevelH4Rejection_Observer startup refused: ", block_reason);
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
      "weekly_level_h4_rejection_v0",
      InpCandidateVersion,
      InpHypothesisHash,
      "W1/D1/H4",
      "H4"
   );
   observation.session_label = CandidateSessionLabel(TimeGMT());
   CandidateApplyPassiveFlags(observation);
   EvaluateWeeklyLevelH4Rejection(observation);
   CandidateApplyCostProjection(observation);
   g_logger.WriteObservation(observation);
}
