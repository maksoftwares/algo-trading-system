#ifndef PHASE1_LIFECYCLE_MQH
#define PHASE1_LIFECYCLE_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1ExpertLifecycleManager
{
private:
   bool m_observe_breakout_retest;
   bool m_observe_swing_breakout_retest;

public:
   void Configure(const bool observe_breakout_retest, const bool observe_swing_breakout_retest)
   {
      m_observe_breakout_retest = observe_breakout_retest;
      m_observe_swing_breakout_retest = observe_swing_breakout_retest;
   }

   Phase1ExpertLifecycleState BreakoutRetestState() const
   {
      if(m_observe_breakout_retest)
         return PHASE1_EXPERT_COST_SUSPENDED;
      return PHASE1_EXPERT_DISABLED;
   }

   string BreakoutRetestStateText() const
   {
      return Phase1ExpertLifecycleText(BreakoutRetestState());
   }

   Phase1ExpertLifecycleState SwingBreakoutRetestState() const
   {
      if(m_observe_swing_breakout_retest)
         return PHASE1_EXPERT_DRY_RUN_ONLY;
      return PHASE1_EXPERT_DISABLED;
   }

   string SwingBreakoutRetestStateText() const
   {
      return Phase1ExpertLifecycleText(SwingBreakoutRetestState());
   }

   bool IsBreakoutRetestDryRunOnly() const
   {
      return BreakoutRetestState() == PHASE1_EXPERT_DRY_RUN_ONLY;
   }

   bool IsBreakoutRetestCostSuspended() const
   {
      return BreakoutRetestState() == PHASE1_EXPERT_COST_SUSPENDED;
   }
};

#endif
