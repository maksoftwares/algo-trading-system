#ifndef CANDIDATE_SESSION_CLOCK_MQH
#define CANDIDATE_SESSION_CLOCK_MQH

string CandidateSessionLabel(const datetime utc_time)
{
   MqlDateTime parts;
   TimeToStruct(utc_time, parts);
   int hour = parts.hour;
   if(hour >= 0 && hour < 6)
      return "ASIA_EARLY";
   if(hour >= 6 && hour < 12)
      return "LONDON";
   if(hour >= 12 && hour < 17)
      return "NY_OVERLAP";
   if(hour >= 17 && hour < 22)
      return "NY_LATE";
   return "ROLLOVER";
}

#endif
