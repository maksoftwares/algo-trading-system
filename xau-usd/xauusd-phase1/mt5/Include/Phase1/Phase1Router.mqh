#ifndef PHASE1_ROUTER_MQH
#define PHASE1_ROUTER_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1Router
{
private:
   bool m_observe_breakout_retest;
   int m_breakout_retest_magic;

public:
   void Configure(const bool observe_breakout_retest, const int breakout_retest_magic)
   {
      m_observe_breakout_retest = observe_breakout_retest;
      m_breakout_retest_magic = breakout_retest_magic;
   }

   bool SelectSignal(Phase1Signal &signal)
   {
      Phase1ResetSignal(signal);

      if(!m_observe_breakout_retest)
      {
         signal.expert_name = "breakout_retest";
         signal.magic_number = m_breakout_retest_magic;
         signal.reason_code = "phase1_observation_disabled";
         signal.blocked_reason = "breakout_retest_observation_disabled";
         return false;
      }

      signal.expert_name = "breakout_retest";
      signal.magic_number = m_breakout_retest_magic;
      signal.reason_code = "approved_future_expert_reserved";
      signal.blocked_reason = "phase1_dry_run_only";
      return false;
   }

   string WouldHaveAllowedExperts() const
   {
      if(m_observe_breakout_retest)
         return "breakout_retest";
      return "none";
   }

   Phase1RegimeState ClassifyRegime(
      const Phase1MarketSnapshot &snapshot,
      const Phase1SessionState session_state,
      const Phase1ExecutionState execution_state,
      const Phase1NewsState news_state
   ) const
   {
      if(news_state != PHASE1_NEWS_NO_RISK)
         return PHASE1_REGIME_NEWS_BLACKOUT;
      if(execution_state != PHASE1_EXECUTION_OK)
         return PHASE1_REGIME_ABNORMAL_MARKET;
      if(session_state == PHASE1_SESSION_WEEKEND || session_state == PHASE1_SESSION_ROLLOVER)
         return PHASE1_REGIME_NO_TRADE;
      if(snapshot.spread_points <= 0.0)
         return PHASE1_REGIME_ABNORMAL_MARKET;
      if(m_observe_breakout_retest)
         return PHASE1_REGIME_BREAKOUT_RETEST;
      return PHASE1_REGIME_NO_TRADE;
   }
};

#endif
