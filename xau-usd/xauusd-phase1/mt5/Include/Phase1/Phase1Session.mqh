#ifndef PHASE1_SESSION_MQH
#define PHASE1_SESSION_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1SessionEngine
{
public:
   Phase1SessionState Detect(const datetime utc_time) const
   {
      MqlDateTime parts;
      TimeToStruct(utc_time, parts);

      if(parts.day_of_week == 0 || parts.day_of_week == 6)
         return PHASE1_SESSION_WEEKEND;
      if(parts.hour >= 21 && parts.hour < 22)
         return PHASE1_SESSION_ROLLOVER;
      if(parts.hour >= 0 && parts.hour < 7)
         return PHASE1_SESSION_ASIA;
      if(parts.hour >= 7 && parts.hour < 13)
         return PHASE1_SESSION_LONDON;
      if(parts.hour >= 13 && parts.hour < 21)
         return PHASE1_SESSION_NEW_YORK;
      return PHASE1_SESSION_THIN;
   }
};

#endif
