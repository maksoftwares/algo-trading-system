#ifndef PHASE1_NEWS_MQH
#define PHASE1_NEWS_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1NewsGuard
{
private:
   bool m_manual_lockdown;

public:
   void Configure(const bool manual_lockdown)
   {
      m_manual_lockdown = manual_lockdown;
   }

   Phase1NewsState Evaluate(const datetime utc_time) const
   {
      if(m_manual_lockdown)
         return PHASE1_NEWS_MANUAL_LOCKDOWN;
      return PHASE1_NEWS_NO_RISK;
   }
};

#endif
