#ifndef PHASE1_LIFECYCLE_MQH
#define PHASE1_LIFECYCLE_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1ExpertLifecycleManager
{
private:
   bool m_observe_breakout_retest;
   bool m_observe_swing_breakout_retest;
   Phase1ExpertLifecycleState m_breakout_retest_family_state;

public:
   CPhase1ExpertLifecycleManager()
   {
      m_observe_breakout_retest = false;
      m_observe_swing_breakout_retest = false;
      m_breakout_retest_family_state = PHASE1_EXPERT_COST_SUSPENDED_CANONICAL;
   }

   void Configure(
      const bool observe_breakout_retest,
      const bool observe_swing_breakout_retest,
      const string breakout_retest_family_cost_state = "COST_SUSPENDED_CANONICAL"
   )
   {
      m_observe_breakout_retest = observe_breakout_retest;
      m_observe_swing_breakout_retest = observe_swing_breakout_retest;
      m_breakout_retest_family_state = ParseBreakoutRetestFamilyCostState(breakout_retest_family_cost_state);
   }

   Phase1ExpertLifecycleState BreakoutRetestState() const
   {
      if(m_observe_breakout_retest)
         return m_breakout_retest_family_state;
      return PHASE1_EXPERT_DISABLED;
   }

   string BreakoutRetestStateText() const
   {
      return Phase1ExpertLifecycleText(BreakoutRetestState());
   }

   Phase1ExpertLifecycleState SwingBreakoutRetestState() const
   {
      if(m_observe_swing_breakout_retest)
         return m_breakout_retest_family_state;
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
      return m_breakout_retest_family_state == PHASE1_EXPERT_COST_SUSPENDED
         || m_breakout_retest_family_state == PHASE1_EXPERT_COST_SUSPENDED_CANONICAL_PENDING_SANITY_CHECK
         || m_breakout_retest_family_state == PHASE1_EXPERT_COST_SUSPENDED_CANONICAL;
   }

   bool IsBreakoutRetestCostRevalidationPending() const
   {
      return m_breakout_retest_family_state == PHASE1_EXPERT_COST_REVALIDATION_PENDING
         || m_breakout_retest_family_state == PHASE1_EXPERT_COST_REVALIDATION_REGENERATED_PENDING_REVIEW;
   }

   bool IsBreakoutRetestFamilyBlockedByCost() const
   {
      return IsBreakoutRetestCostRevalidationPending() || IsBreakoutRetestCostSuspended();
   }

   string BreakoutRetestFamilyBlockReason() const
   {
      const string state = Phase1ExpertLifecycleText(m_breakout_retest_family_state);
      if(IsBreakoutRetestCostSuspended() || IsBreakoutRetestCostRevalidationPending())
         return state;
      return "";
   }

private:
   Phase1ExpertLifecycleState ParseBreakoutRetestFamilyCostState(const string state_text) const
   {
      if(state_text == "COST_SUSPENDED")
         return PHASE1_EXPERT_COST_SUSPENDED;
      if(state_text == "COST_SUSPENDED_CANONICAL_PENDING_SANITY_CHECK")
         return PHASE1_EXPERT_COST_SUSPENDED_CANONICAL_PENDING_SANITY_CHECK;
      if(state_text == "COST_SUSPENDED_CANONICAL")
         return PHASE1_EXPERT_COST_SUSPENDED_CANONICAL;
      if(state_text == "COST_REVALIDATION_REGENERATED_PENDING_REVIEW")
         return PHASE1_EXPERT_COST_REVALIDATION_REGENERATED_PENDING_REVIEW;
      if(state_text == "COST_REVALIDATION_PENDING")
         return PHASE1_EXPERT_COST_REVALIDATION_PENDING;
      if(state_text == "DRY_RUN_APPROVED" || state_text == "DRY_RUN_ONLY")
         return PHASE1_EXPERT_DRY_RUN_ONLY;
      if(state_text == "RETIRED")
         return PHASE1_EXPERT_RETIRED;
      return PHASE1_EXPERT_COST_SUSPENDED_CANONICAL;
   }
};

#endif
