#ifndef PHASE1_LOGGER_MQH
#define PHASE1_LOGGER_MQH

#include <Phase1/Phase1Types.mqh>

class CPhase1CsvLogger
{
private:
   string m_file_name;

public:
   void Configure(const string file_name)
   {
      m_file_name = file_name;
   }

   bool WriteHeartbeat(
      const string run_id,
      const string lifecycle_state,
      const string symbol_name,
      const datetime bar_time,
      const double bid,
      const double ask,
      const double spread_points,
      const bool spread_ok,
      const Phase1Signal &signal
   )
   {
      int handle = FileOpen(
         m_file_name,
         FILE_CSV | FILE_READ | FILE_WRITE | FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_ANSI,
         ','
      );
      if(handle == INVALID_HANDLE)
      {
         Print("Phase1 logger could not open file: ", m_file_name, " error=", GetLastError());
         return false;
      }

      if(FileSize(handle) == 0)
      {
         FileWrite(
            handle,
            "timestamp_utc",
            "run_id",
            "lifecycle_state",
            "symbol",
            "bar_time",
            "bid",
            "ask",
            "spread_points",
            "spread_ok",
            "expert_name",
            "magic_number",
            "direction",
            "entry_price",
            "stop_loss",
            "take_profit",
            "risk_pct",
            "reason_code",
            "blocked_reason"
         );
      }

      FileSeek(handle, 0, SEEK_END);
      FileWrite(
         handle,
         TimeToString(TimeGMT(), TIME_DATE | TIME_SECONDS),
         run_id,
         lifecycle_state,
         symbol_name,
         TimeToString(bar_time, TIME_DATE | TIME_SECONDS),
         DoubleToString(bid, _Digits),
         DoubleToString(ask, _Digits),
         DoubleToString(spread_points, 2),
         spread_ok ? "true" : "false",
         signal.expert_name,
         signal.magic_number,
         Phase1DirectionText(signal.direction),
         DoubleToString(signal.entry_price, _Digits),
         DoubleToString(signal.stop_loss, _Digits),
         DoubleToString(signal.take_profit, _Digits),
         DoubleToString(signal.risk_pct, 4),
         signal.reason_code,
         signal.blocked_reason
      );
      FileClose(handle);
      return true;
   }
};

#endif
