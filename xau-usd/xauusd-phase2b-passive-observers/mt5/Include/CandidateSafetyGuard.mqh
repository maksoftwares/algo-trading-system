#ifndef CANDIDATE_SAFETY_GUARD_MQH
#define CANDIDATE_SAFETY_GUARD_MQH

#include "CandidateObserverCommon.mqh"

bool CandidateStartupGuard(
   const bool dry_run_only,
   const string symbol_name,
   const string target_symbol,
   const bool allow_research_symbol_override,
   string &block_reason
)
{
   if(!dry_run_only)
   {
      block_reason = "dry_run_only_input_disabled";
      return false;
   }

   if(symbol_name != target_symbol && !allow_research_symbol_override)
   {
      block_reason = "symbol_not_xauusd";
      return false;
   }

   block_reason = "none";
   return true;
}

void CandidateApplyPassiveFlags(CandidateObservation &observation)
{
   observation.dry_run = true;
   observation.trade_permission = false;
   observation.broker_action_allowed = false;
   observation.phase2_execution_authorized = false;
}

#endif
