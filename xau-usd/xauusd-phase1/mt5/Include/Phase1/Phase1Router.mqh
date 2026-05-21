#ifndef PHASE1_ROUTER_MQH
#define PHASE1_ROUTER_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1Router
{
private:
   bool m_allow_breakout_retest;

public:
   void Configure(const bool allow_breakout_retest)
   {
      m_allow_breakout_retest = allow_breakout_retest;
   }

   bool SelectSignal(Phase1Signal &signal)
   {
      Phase1ResetSignal(signal);

      if(!m_allow_breakout_retest)
      {
         signal.expert_name = "breakout_retest";
         signal.magic_number = 910100;
         signal.reason_code = "phase0_gate9_pending";
         signal.blocked_reason = "manual_adversarial_review_incomplete";
         return false;
      }

      signal.expert_name = "breakout_retest";
      signal.magic_number = 910100;
      signal.reason_code = "expert_slot_reserved";
      signal.blocked_reason = "expert_logic_not_implemented_in_phase1";
      return false;
   }
};

#endif
