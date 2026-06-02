#ifndef CANDIDATE_CSV_LOGGER_MQH
#define CANDIDATE_CSV_LOGGER_MQH

#include "CandidateObserverCommon.mqh"

class CCandidateCsvLogger
{
private:
   string m_file_name;

public:
   void Configure(const string file_name)
   {
      m_file_name = file_name;
   }

   bool EnsureHeader()
   {
      int handle = OpenCsv();
      if(handle == INVALID_HANDLE)
         return false;
      if(FileSize(handle) == 0)
         FileWriteString(handle, Header() + "\r\n");
      FileFlush(handle);
      FileClose(handle);
      return true;
   }

   bool WriteObservation(const CandidateObservation &observation)
   {
      int handle = OpenCsv();
      if(handle == INVALID_HANDLE)
         return false;
      if(FileSize(handle) == 0)
         FileWriteString(handle, Header() + "\r\n");
      FileSeek(handle, 0, SEEK_END);

      string row = "";
      AppendCell(row, observation.timestamp_utc);
      AppendCell(row, observation.timestamp_broker);
      AppendCell(row, observation.timestamp_local);
      AppendCell(row, observation.run_id);
      AppendCell(row, observation.candidate_id);
      AppendCell(row, observation.candidate_version);
      AppendCell(row, observation.hypothesis_hash);
      AppendCell(row, observation.symbol);
      AppendCell(row, observation.timeframe_decision);
      AppendCell(row, observation.timeframe_entry);
      AppendCell(row, DoubleToString(observation.bid, observation.digits));
      AppendCell(row, DoubleToString(observation.ask, observation.digits));
      AppendCell(row, DoubleToString(observation.spread_points, 2));
      AppendCell(row, DoubleToString(observation.point_size, 8));
      AppendCell(row, IntegerToString(observation.digits));
      AppendCell(row, observation.session_label);
      AppendCell(row, observation.news_state_if_available);
      AppendCell(row, observation.candidate_state);
      AppendCell(row, CandidateBoolText(observation.would_signal));
      AppendCell(row, observation.signal_direction);
      AppendCell(row, DoubleToString(observation.theoretical_entry, observation.digits));
      AppendCell(row, DoubleToString(observation.theoretical_sl, observation.digits));
      AppendCell(row, DoubleToString(observation.theoretical_tp_1_5r, observation.digits));
      AppendCell(row, DoubleToString(observation.theoretical_tp_2_0r, observation.digits));
      AppendCell(row, DoubleToString(observation.stop_distance_points, 2));
      AppendCell(row, DoubleToString(observation.measured_median_spread_points, 2));
      AppendCell(row, DoubleToString(observation.measured_p95_spread_points, 2));
      AppendCell(row, DoubleToString(observation.projected_cost_r_median, 4));
      AppendCell(row, DoubleToString(observation.projected_cost_r_p95, 4));
      AppendCell(row, DoubleToString(observation.projected_net_r_floor_assumption, 4));
      AppendCell(row, CandidateBoolText(observation.cost_feasible));
      AppendCell(row, CandidateBoolText(observation.same_family_as_breakout_retest));
      AppendCell(row, CandidateBoolText(observation.dry_run));
      AppendCell(row, CandidateBoolText(observation.trade_permission));
      AppendCell(row, CandidateBoolText(observation.broker_action_allowed));
      AppendCell(row, CandidateBoolText(observation.phase2_execution_authorized));
      AppendCell(row, observation.block_reason);
      AppendCell(row, observation.notes);
      FileWriteString(handle, row + "\r\n");
      FileFlush(handle);
      FileClose(handle);
      return true;
   }

private:
   int OpenCsv() const
   {
      int handle = FileOpen(
         m_file_name,
         FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_SHARE_WRITE
      );
      if(handle == INVALID_HANDLE)
         Print("Candidate observer could not open CSV file: ", m_file_name, " error=", GetLastError());
      return handle;
   }

   string Header() const
   {
      return "timestamp_utc,timestamp_broker,timestamp_local,run_id,candidate_id,candidate_version,hypothesis_hash,symbol,timeframe_decision,timeframe_entry,bid,ask,spread_points,point_size,digits,session_label,news_state_if_available,candidate_state,would_signal,signal_direction,theoretical_entry,theoretical_sl,theoretical_tp_1_5r,theoretical_tp_2_0r,stop_distance_points,measured_median_spread_points,measured_p95_spread_points,projected_cost_r_median,projected_cost_r_p95,projected_net_r_floor_assumption,cost_feasible,same_family_as_breakout_retest,dry_run,trade_permission,broker_action_allowed,phase2_execution_authorized,block_reason,notes";
   }

   string CsvCell(const string value) const
   {
      string cell = value;
      StringReplace(cell, "\"", "\"\"");
      if(StringFind(cell, ",") >= 0 || StringFind(cell, "\"") >= 0 || StringFind(cell, "\r") >= 0 || StringFind(cell, "\n") >= 0)
         return "\"" + cell + "\"";
      return cell;
   }

   void AppendCell(string &row, const string value) const
   {
      if(row != "")
         row += ",";
      row += CsvCell(value);
   }
};

#endif
