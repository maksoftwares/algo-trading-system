#ifndef PHASE1_SERVER_TIME_MQH
#define PHASE1_SERVER_TIME_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1ServerTimeValidator
{
private:
   int m_expected_local_utc_offset_hours;
   int m_max_clock_drift_seconds;

public:
   void Configure(const int expected_local_utc_offset_hours, const int max_clock_drift_seconds)
   {
      m_expected_local_utc_offset_hours = expected_local_utc_offset_hours;
      m_max_clock_drift_seconds = max_clock_drift_seconds;
   }

   bool Validate(const Phase1MarketSnapshot &snapshot, Phase1ServerTimeStatus &status) const
   {
      Phase1ResetServerTimeStatus(status);
      status.broker_utc_offset_seconds = (long)(snapshot.broker_time - snapshot.utc_time);
      status.local_utc_offset_seconds = (long)(snapshot.local_time - snapshot.utc_time);

      long expected_offset_seconds = (long)m_expected_local_utc_offset_hours * 3600;
      status.local_clock_drift_seconds = status.local_utc_offset_seconds - expected_offset_seconds;
      status.clock_ok = (MathAbs((double)status.local_clock_drift_seconds) <= m_max_clock_drift_seconds);
      status.status_text = status.clock_ok ? "CLOCK_OK" : "LOCAL_CLOCK_DRIFT";
      return status.clock_ok;
   }
};

#endif
